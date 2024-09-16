from main.models import models
from main.tools.analyzed_samples import update_query_for_negatives


def queries(many, one):
    """This is to create django queries resulting in a m:1 datasheet.
    start = the m column, like site
    end =  the 1 column, like sample

    To construct the datasheet we need to filter the 1 objects for the m object,
    thus this function returns the queries required by generic.py get_dataset function.

    Example: queries(site, library), we go to site from library via sample --> sample__site
    """
    dict = {
        ("site", "library"): "sample__site",
        ("site", "sample"): "site",
        ("site", "layer"): "site",
        (
            "site",
            "date",
        ): "layer_model__site",  # TODO: make sure that dates added to a sample are added to the layer automatically!
        ("project", "library"): "project",
        ("project", "sample"): "project",
        ("project", "site"): "project",
        ("project", "layer"): "site__project",
        ("project", "contact"): "site__project",
        ("project", "quicksand_analysis"): "analyzedsample__sample__project",
        ("site", "quicksand_analysis"): "analyzedsample__sample__site",
    }

    return dict[(many, one)]


def get_querysets(many, unique, start):
    """
    This is the updated version - more manual, but allows for exceptions in the queryset pick
    """
    if unique == "quicksand_analysis":
        # we first need to get all the analyze_samples that we need,
        # then update to include the negative controls
        filter = {queries(many, "library"): start}
        qs = update_query_for_negatives(
            models["library"].objects.filter(**filter).distinct()
        )
        # only then return the actual quicksand dataset
        return models["quicksand_analysis"].objects.filter(analyzedsample__in=qs)
