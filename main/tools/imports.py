import pandas as pd
import numpy as np
from .. import models

# when importing, take care of layer names! also: if  sublayers have the same colour as parent layer, apply parent layer colouration to sublayer
def update_colour_from_tsv(file_path:str, column_name=3, column_colour_m=6, column_site_name=1):
    df = pd.read_csv(file_path, sep="\t")
    for i in range(1, len(df.index)):
        print(i)
        if df.iat[i, column_site_name] is np.nan:
            continue

        site = models.Site.objects.filter(name=df.iat[i, column_site_name])
        if site.exists():
            site = site[0]
        else:
            continue

        # still needs to be able to deal with sublayers (layer_name*)
        layer = models.Layer.objects.filter(site=site, name=df.iat[i,column_name])
        if layer.exists():
            layer = layer[0]
            if df.iat[i,5] != "":
                layer.colour = df.iat[i,5]
            if df.iat[i,column_colour_m] != "":
                layer.colour_munsell = df.iat[i,column_colour_m]
            layer.save()
        else:
            print("Layer " + str(df.iat[i,column_name]) + " does not exist")
