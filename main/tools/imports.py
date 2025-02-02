import pandas as pd
import numpy as np
from .. import models

# when importing, take care of layer names! also: if  sublayers have the same colour as parent layer, apply parent layer colouration to sublayer
def update_colour_from_tsv(file_path:str, column_name=3, column_colour_m=6, column_site_name=1):
    df = pd.read_csv(file_path, sep="\t")
    for i in range(1, len(df.index)):
        print(i)
        if df.iat[i, column_site_name] is np.nan or df.iat[i, column_colour_m] is np.nan or df.iat[i, column_colour_m] == "manual review":
            print("no color given")
            continue

        site = models.Site.objects.filter(name=df.iat[i, column_site_name])
        if site.exists():
            site = site[0]
        else:
            print("site does not exist")
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

def update_texture_from_tsv(file_path:str, column_layer_name=3, column_texture=7, column_site_name=1):
    df = pd.read_csv(file_path, sep="\t")
    for i in range(1, len(df.index)):
        print(i)
        if df.iat[i, column_site_name] is np.nan or df.iat[i, column_texture] is np.nan:
            continue

        site = models.Site.objects.filter(name=df.iat[i, column_site_name])
        if site.exists():
            site = site[0]
        else:
            #print("site does not exist")
            continue

        layer = models.Layer.objects.filter(site=site, name=df.iat[i, column_layer_name])
        if layer.exists():
            layer = layer[0]
            if df.iat[i, column_texture] != "":
                layer.texture = df.iat[i, column_texture]
                print(layer.texture)
            layer.save()
        else:
            #print("Layer " + str(df.iat[i, column_layer_name]) + " does not exist")
            continue


#for testing only! dont use!
def import_from_csv(file_path:str):
    df = pd.read_csv(file_path)
    for i in range(0,len(df.index)):
        #create site instance
        if df.iat[i,1] is np.nan:
            #print("skip line: nan")
            continue
        site, created = models.Site.objects.get_or_create(name=df.iat[i,1],
                                          coredb_id=df.iat[i,2],
                                          country=df.iat[i,3])

        if created or not site.profile.exists() or site.profile.name == "":
            profile = models.Profile.objects.create(name="Main " + site.name, site=site)
            profile.save()
            print("created new profile")

        #create layers
        layer = models.Layer.objects.filter(name=df.iat[i,5], site=site)
        if not layer.exists():
            layer = models.Layer.objects.create(name=df.iat[i,5],
                                                         #description=df.iat[i,16], #sample location
                                                                site=site,
                                                                pos=len(site.layer.all()))
            layer.pos = len(site.layer.all())
            layer.save()
            layer.profile.set(models.Profile.objects.filter(site=layer.site))
            print("created layer " + str(layer.name) + " at " + site.name)
        else:
            layer = layer[0]