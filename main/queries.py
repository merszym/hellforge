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
        ("site", "layer"): "site",
        ("project", "site"): "project",
        ("project", "layer"): "site__project",
        ("project", "contact"): "site__project",
        ("site", "profilelayerjunction"): "profile__site",
    }

    return dict[(many, one)]


def get_queryset(start, unique, authenticated=False, project=None):
    # return for a set of objects for a given start point and value of interest
    try:
        filter = {queries(start.model, unique): start}
        return models[unique].objects.filter(**filter).distinct()
    except:
        pass

    # start from a site
    if start.model == "site":
        # if not authenticated, restrict to the entries that are part of the project
        if unique == "date":
            #export unpublished dates only if authenticated
            return start.get_dates(without_reference=authenticated)
        if unique == 'sample':
            qs = models['sample'].objects.filter(
                Q(site=start)
                & Q(domain='mpi_eva')
            )
            if not authenticated:
                qs = qs.filter(project=project)
            return qs
        if unique == 'analyzedsample':
            qs = models['analyzedsample'].objects.filter(sample__site=start)
            if not authenticated:
                qs = qs.filter(project=project)
            return update_query_for_negatives(qs)

    # start from a project
    if start.model == 'project':
        if unique == 'sample':
            return models['sample'].objects.filter(
                Q(site__project=start)
                & Q(project=start)
                & Q(domain='mpi_eva')
            )
        if unique == "analyzedsample":
            qs = models['analyzedsample'].objects.filter(
                Q(sample__site__project=start)
                & Q(sample__project=start)
                & Q(project=start)
            )
            return update_query_for_negatives(qs, project=start)
        if unique == 'author':
            # a person can appear multiple times if author on several sites
            # so return distinct
            qs = models['person'].objects.filter(
                Q(author__description__project=start) |
                Q(author__description__project_project=start)
            ).distinct()
            print(qs)
            return qs
        # see if the generic queries work
        filter = {queries(start.model, unique): start}
        return models[unique].objects.filter(**filter).distinct()
