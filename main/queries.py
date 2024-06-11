from main.models import models


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
        ("project", "library"): "project",
        ("project", "sample"): "project",
        ("project", "site"): "project",
        ("project", "layer"): "site__project",
        ("project", "contact"): "site__project",
    }

    return dict[(many, one)]
