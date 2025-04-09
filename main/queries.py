from main.models import models
from main.tools.analyzed_samples import update_query_for_negatives
from django.db.models import Q


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
        ("site", "profilelayerjunction"): "profile__site",
    }

    return dict[(many, one)]


def get_project_authors(project):
    """
    Get project authors (via description)
    """
    qs = models['person'].objects.filter(
        Q(author__description__project=project) |
        Q(author__description__project_project=project)
    )
    # a person can appear multiple times if author on several sites
    # so return distinct
    return qs.distinct()


def get_project_samples(project):
    """
    The more controlled query to get the project_samples query. This is necessary, because the automated one is too buggy...
    """
    qs = models['sample'].objects.filter(
            Q(site__project=project)
            & Q(project=project)
        )
    return qs


def get_libraries(start):
    """
    The more controlled query to get the libraries query. This is necessary, because the automated one is too buggy...
    """
    if start.model == 'site':
        qs = models['analyzedsample'].objects.filter(sample__site=start)
        qs = update_query_for_negatives(qs)
        return qs
    if start.model == 'project':
        qs = models['analyzedsample'].objects.filter(
                Q(sample__site__project=start)
                & Q(sample__project=start)
                & Q(project=start)
            )
        qs = update_query_for_negatives(qs, project=start)
        return qs
