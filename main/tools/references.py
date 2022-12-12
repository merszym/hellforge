from main.models import Reference
import numpy as np
from django.db.models import Q

def find(kw):
    #find the best reference for a given search term
    if kw==kw:
        if ref := Reference.objects.filter(Q(short=kw) | Q(doi=kw)).first():
                return ref
        return 'Not Found'
    return np.nan
