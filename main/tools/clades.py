## the mammalian per-family analysis: estimated counts per reference genome (kallisto), summed per clade
## the genome -> clade assignment (CladeReference) is uploaded in the admin
import re
import pandas as pd
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render
from django.urls import path
from main.tools.generic import get_instance_from_string
from main.models import AnalyzedSample, Sample, FamilyAnalysis

# the columns of one genome (one line per genome), all other columns are the same for the library/sample (run information)
GENOME_COLUMNS = ["target_id", "length", "eff_length", "est_counts", "tpm"]
ID_COLUMNS = ["library", "sample", "bowtie2_name"]


def get_library(library, runid, seqpool):
    """the analyzed sample of the library/capture id in this sequencing run and pool (as in the quicksand upload)"""
    if library.startswith("Lib"):
        try:
            return AnalyzedSample.objects.get(library=library, seqrun=runid, seqpool=seqpool)
        except AnalyzedSample.DoesNotExist:  # could be a reamp library
            return AnalyzedSample.objects.get(reamp_library=library, seqrun=runid, seqpool=seqpool)
    if library.startswith("Cap") or library.startswith("ERR"):
        return AnalyzedSample.objects.get(capture=library, seqrun=runid, seqpool=seqpool)
    # a random library/capture identifier
    return AnalyzedSample.objects.get(Q(library=library) | Q(capture=library), seqrun=runid, seqpool=seqpool)


def handle_clade_report(request, file):
    """
    the counts-per-genome sheet of one family (bowtie2_name), several libraries and/or samples (merged data):
    each line has either a 'library' (with the sequencing run and pool of the form) or a 'sample' (name, of this site).
    for a sample, all its libraries with the probe of the form are linked as the merged libraries.
    a new upload replaces the result of the library/sample and family
    """
    site = get_instance_from_string(request.POST.get("object"))

    def done(level, text):
        messages.add_message(request, level, text)
        return render(request, "main/modals/site_modal.html", {"object": site, "type": "clade_upload"})

    runid = request.POST.get("sequencing", False)
    seqpool = request.POST.get("seqpool", False)
    version = request.POST.get("version", "").strip()
    # a version (v2.1) or a git commit hash (bace0a0)
    if not re.fullmatch(r"v[0-9]+(\.[0-9]+)*|[0-9a-fA-F]{7,40}", version):
        return done(messages.ERROR, "Version missing or wrong format")

    try:
        df = pd.read_csv(file, sep="\t")
    except Exception as e:
        return done(messages.ERROR, f"The file could not be read: {e}")
    missing = {"bowtie2_name", "target_id", "est_counts"} - set(df.columns)
    if "library" not in df.columns and "sample" not in df.columns:
        missing.add("library/sample")
    if missing:
        return done(messages.ERROR, f"Columns missing: {', '.join(sorted(missing))}")
    families = df["bowtie2_name"].dropna().unique()
    if len(families) != 1:
        return done(messages.ERROR, f"The file must contain exactly one family (bowtie2_name), found: {', '.join(map(str, families)) or 'none'}")
    family = str(families[0]).capitalize()  # hyaenidae -> Hyaenidae

    for column in ["library", "sample"]:
        df[column] = df[column].fillna("").astype(str).str.strip() if column in df.columns else ""
    if (df["library"] != "").any() and not runid:
        return done(messages.ERROR, "Sequencing ID is missing (needed for the libraries)")

    probe = request.POST.get("probe", "")  # merged data: the libraries of the sample with this probe

    imported, not_found = [], []
    for (library, sample), report in df.groupby(["library", "sample"]):
        name = library or sample
        try:
            if library and sample:
                raise ValueError("library and sample given")
            if library:
                target = {"analyzedsample": get_library(library, runid, seqpool)}
            elif sample:
                target = {"sample": Sample.objects.get(name=sample, site=site)}
            else:
                raise ValueError("no library or sample")
        except Exception:
            not_found.append(name or "(empty)")
            continue
        first = report.iloc[0]
        meta = {k: (None if pd.isna(v) else (v.item() if hasattr(v, "item") else v))
                for k, v in first.items() if k not in GENOME_COLUMNS + ID_COLUMNS}
        data = {str(row.target_id): float(row.est_counts) for row in report.itertuples()}
        analysis, created = FamilyAnalysis.objects.update_or_create(
            family=family, **target, defaults={"version": version, "meta": meta, "data": data}
        )
        if sample:
            libraries = AnalyzedSample.objects.filter(sample=target["sample"], probes=probe) if probe else []
            analysis.libraries.set(libraries)
            name = f"{sample} ({len(libraries)} {probe or 'no probe'} libraries)"
        imported.append(name)

    if not_found:
        messages.add_message(request, messages.WARNING, f"{', '.join(not_found)}: not found in the database, ignored for upload")
    if imported:
        messages.add_message(request, messages.SUCCESS, f"{family}: {', '.join(imported)}: Upload successful")
    return render(request, "main/modals/site_modal.html", {"object": site, "type": "clade_upload"})


#
# the clade table (sub-tab of the Mammalian mtDNA tab): uses the filters and settings of quicksand
#

SINK = "sink"  # genomes without clade, not in the percentages


def filter_clades(analysis, reference, settings):
    """
    the clades of a result with the filters of the settings (quicksand settings of the DNA tab):
    returns (valid, {clade: est_counts} of the clades passing the cutoffs, est_counts with clade, est_counts in the sink)
    """
    counts = analysis.clade_counts(reference)
    sink = counts.pop(SINK, 0)
    total = sum(counts.values())
    # at least the required number of unique sequences (n_pseudoaligned of kallisto)
    if (analysis.meta or {}).get("n_pseudoaligned", 0) < settings["clademinseqs"]:
        return False, {}, total, sink
    # too many estimated counts in the sink (relative to the counts with clade): the result is not valid
    if not total or sink / total >= settings["cladesinkratio"]:
        return False, {}, total, sink
    # only the clades with at least the estimated counts and the percentage (of the estimated counts with clade)
    counts = {clade: n for clade, n in counts.items()
              if n > 0 and n >= settings["clademincounts"] and 100 * n / total >= settings["cladepercent"]}
    return True, counts, total, sink


def clade_rows(request, site):
    """
    the clade results of one family, one row per result (library or sample with its merged libraries).
    a result is shown if (one of) its libraries passes the filters of the DNA tab.
    the family: the first selected family of quicksand with clade results (the chips of quicksand and clades are the same)
    """
    from main.tools.analyzed_samples import get_libraries, sort_libraries, LIBRARY_LAYER_RELATED
    from main.tools.dna_filters import get_analysis_settings
    from main.tools.projects import get_project
    from main.tools.quicksand import prepare_data
    from main.models import QuicksandAnalysis, CladeReference

    settings = get_analysis_settings(request, "quicksand")
    libraries = get_libraries(request, site.pk, return_query=True).filter(qc_pass=True)
    if settings["only_project"]:
        libraries = libraries.filter(project=get_project(request))
    order = {pk: i for i, pk in enumerate(sort_libraries(request, libraries, site, default="layer").values_list("pk", flat=True))}

    # the families that are ancient (++) in quicksand (with the cutoffs of the quicksand settings)
    quicksand = prepare_data(
        request, QuicksandAnalysis.objects.filter(analyzedsample__in=libraries).select_related("analyzedsample"),
        column=settings["column"], percentage=settings["percentage"], breadth=settings["breadth"],
        ancient=True, only_project=settings["only_project"],
    )
    found = {}
    for entry, families in quicksand["quicksand_results"].items():
        found.setdefault(entry.analyzedsample_id, set()).update(families)

    results = FamilyAnalysis.objects.filter(Q(analyzedsample__in=libraries) | Q(libraries__in=libraries)).distinct()
    families = sorted(set(results.values_list("family", flat=True)))
    family = next((f for f in settings["family"] if f in families), families[0] if families else None)

    rows = []
    query = results.filter(family=family).select_related(
        *[f"analyzedsample__{x}" for x in LIBRARY_LAYER_RELATED], *LIBRARY_LAYER_RELATED
    ).prefetch_related("libraries", "sample__image_annotations", "analyzedsample__sample__image_annotations")  # eye-icon
    reference = CladeReference.latest(family) if family else None
    for analysis in query:
        libs = [analysis.analyzedsample] if analysis.analyzedsample else [l for l in analysis.libraries.all() if l.pk in order]
        if not libs:
            continue
        in_quicksand = any(family in found.get(lib.pk, ()) for lib in libs)
        if settings["cladelinked"] and not in_quicksand:
            continue
        valid, counts, total, sink = filter_clades(analysis, reference, settings)
        if not valid:
            continue
        shown = sum(counts.values())
        clades = {clade: {"raw": n, "percent": 100 * n / shown} for clade, n in counts.items()}
        rows.append({
            "analysis": analysis,
            "sample": analysis.sample or analysis.analyzedsample.sample,
            "libraries": libs,
            "probes": sorted({lib.probes or "" for lib in libs}),
            "seqruns": sorted({lib.seqrun for lib in libs}),
            "quicksand": in_quicksand,
            "total": total,
            "shown": shown,
            "sink": sink,
            "clades": dict(sorted(clades.items(), key=lambda x: -x[1]["raw"])),
            "position": min(order[lib.pk] for lib in libs),
        })
    rows.sort(key=lambda row: row["position"])
    # bar-view: the length of the bars relative to the highest estimated counts (as the families in quicksand)
    maxsum = max([row["shown"] for row in rows], default=0)
    for row in rows:
        for value in row["clades"].values():
            value["display"] = 100 * value["raw"] / maxsum

    # the colors from the palette of the reference (in its order), clades without color: grey
    palette = (reference.color_palette or {}) if reference else {}
    present = {clade for row in rows for clade in row["clades"]}
    columns = [c for c in palette if c in present] + sorted(present - palette.keys())
    colors = [(clade, palette.get(clade, "#bbbbbb")) for clade in columns]
    return {
        "rows": rows,
        "families": families,
        "family": family,
        "reference": reference,
        "colors": colors,
        "colors_dict": dict(colors),
        "tableview": settings["tableview"],
        "cladelinked": settings["cladelinked"],
        "cladepercent": settings["cladepercent"],
        "clademinseqs": settings["clademinseqs"],
        "clademincounts": settings["clademincounts"],
        "cladesinkratio": settings["cladesinkratio"],
        "ancient": settings["ancient"],
    }


def get_clade_tab(request, pk):
    from main.models import Site

    site = Site.objects.get(pk=int(pk))
    context = {"object": site}
    context.update(clade_rows(request, site))
    return render(request, "main/clades/clades-content.html", context)


urlpatterns = [
    path("get-table/<int:pk>", get_clade_tab, name="main_site_getclades"),
]
