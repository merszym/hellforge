from main.models import Reference, models
from main.forms import ReferenceForm
import re
import requests
import numpy as np
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)  # this is for now, make smarter later


def write_bibliography(references):
    # this function needs citeproc and citeproc_styles
    from io import StringIO
    from citeproc.source.bibtex import BibTeX

    # Import the citeproc-py classes we'll use below.
    from citeproc import CitationStylesStyle, CitationStylesBibliography
    from citeproc import formatter
    from citeproc import Citation, CitationItem
    from citeproc_styles import get_style_filepath

    # I assume, that the references are all containing a bibtex field...
    bibs = "\n".join(x.bibtex for x in references)
    bib_source = BibTeX(StringIO(bibs))
    
    # import chicago style sheet
    style_path = get_style_filepath('chicago-author-date')
    bib_style = CitationStylesStyle(style_path)
    
    bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.html)
    
    # now register all references
    ## this dict is to store the in-text references e.g. (Müller et al, 2020)
    short_dict = {}

    for ref in references:
        try:
            cit = Citation([CitationItem(f'reference_{ref.pk}')])
            bibliography.register(cit)
            short_dict[ref.pk] = bibliography.cite(cit, print("Warn:Reference not yet with bibtex"))
        except TypeError:
            pass

    try:
        return [str(item) for item in bibliography.bibliography()], short_dict
    except TypeError:
        return []
        
    

def bibtex_replace_key(bibtex, pk):
    bibtex_mod = re.sub(r"\{(.*?),",fr"{{reference_{pk},",bibtex, 1)
    return bibtex_mod.strip()


def doi2bib(doi, pk):
    """
    - This function accesses the doi.org webpage to retrieve the bib-tex entry for a given doi, 
    - then replaces the tag with the entry ID
    - returns the bibtex as string
    """
    if doi.startswith("10"): 
        content = requests.get(f"https://www.doi.org/{doi}", headers={"Accept":"application/x-bibtex"}).content.decode('UTF-8')
        # replace the tag with the pk, so that it is always unique!
        return bibtex_replace_key(content, pk)
        

def find(kw):
    # find the best reference for a given search term
    if kw == kw:
        if ref := Reference.objects.filter(Q(short=kw) | Q(doi=kw)).first():
            return ref
        return "Not Found"
    return None


def get_modal(request):
    return render(
        request,
        "main/reference/reference-searchinput.html",
        {"origin": "editorjs", "editor": True},
    )


def get_popup(request):
    pk = int(request.GET.get("pk", False))
    obj = Reference.objects.get(pk=pk)
    reference_items, short_dict = write_bibliography([obj])
    
    context = {"ref": obj, "pos": "right"}

    if title := request.GET.get("title", False):
        if pk in short_dict:
            context.update({"title": short_dict[pk]})
        else: 
            context.update({"title": title})
    return render(request, "main/reference/reference-popup.html", context)


## References ##
class ReferenceCreateView(LoginRequiredMixin, CreateView):
    model = Reference
    form_class = ReferenceForm
    template_name = "main/reference/reference_form.html"


class ReferenceUpdateView(LoginRequiredMixin, UpdateView):
    model = Reference
    form_class = ReferenceForm
    template_name = "main/reference/reference_form.html"


urlpatterns = [
    path("modal", get_modal, name="ajax_ref_modal_get"),
    path("popup", get_popup, name="ajax_ref_popup_get"),
    path("create", ReferenceCreateView.as_view(), name="ref_add"),
    path("edit/<int:pk>", ReferenceUpdateView.as_view(), name="ref_update"),
]
