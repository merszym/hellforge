#from colour.examples.notation.examples_munsell import munsell_colour
#from weasyprint.css.computed_values import length
from unicodedata import category

from main.models import ColourName, ColourMunsell, Layer, Site, TextureCategory, TextureKeyword
from main.forms import ReferenceForm, LayerColourForm
import csv

#add input string cleanup before creation!
def import_colours_from_csv(path):
    with open(path) as file:
        reader = csv.reader(file, delimiter="\t")
        for row in reader:
            name_new, created = ColourName.objects.get_or_create(
                name=row[0]
            )
            if created:
                name_new.is_default = False if len(row) < 4 else row[3].strip().lower()=="true"
                name_new.save()
            _ ,created_m = ColourMunsell.objects.get_or_create(
                colour_munsell=row[1],
            )
            _.is_default = False if len(row) < 3 else row[2].strip().lower()=="true"
            _.colour_name.add(name_new)
            _.save()

def update_layer_colours_new(path):
    with open(path) as file:
        reader = csv.reader(file, delimiter="\t")
        for row in reader:
            colour_keyword = row[13]
            if colour_keyword != "":
                site = Site.objects.filter(name=row[0])
                if site.exists():
                    layer = Layer.objects.filter(name=row[2], site=site[0])
                    if layer.exists():
                        layer = layer.first()
                        if colour_keyword[0].isdigit():  # is colour keyword a munsell value?
                            new_colour_munsell = ColourMunsell.objects.filter(colour_munsell=colour_keyword)
                            if new_colour_munsell.exists():
                                new_colour_munsell_entry = new_colour_munsell[0]
                                layer.colour_munsell = new_colour_munsell_entry
                                layer.save()
                            else:
                                print("Munsell value " + colour_keyword + " does not exist.")
                                continue
                        else:
                            new_colour_name = ColourName.objects.filter(name=colour_keyword)
                            if new_colour_name.exists():
                                new_colour_name_entry = new_colour_name[0]
                                layer.colour = new_colour_name_entry
                                layer.save()
                            else:
                                print("Colour " + colour_keyword + " does not exist.")
                                continue
                    else:
                        print("Layer " + row[2] + " of site " + row[0] + " does not exist.")
                        continue
                else:
                    print("Site " + row[0] + " does not exist.")
                    continue

#for initially creating category database entries
def make_texture_db():
    categories = ["silty clay",
                  "sandy clay loam",
                  "silty clay loam",
                  "clay loam",
                  "sandy loam",
                  "silt loam",
                  "loam",
                  "silt",
                  "loamy sand",
                  "sand",
                  "clay",
                  "sandy clay"]
    for entry in categories:
        new_cat, created = TextureCategory.objects.get_or_create(category=entry)
        new_cat.save()

#for adding keywords and pairing to categories
def update_textures(path):
    with open(path) as file:
        reader = csv.reader(file, delimiter="\t")
        for row in reader:
            print(row)
            new_keyword, created = TextureKeyword.objects.get_or_create(
                texture = row[0],
                texture_category  = TextureCategory.objects.get(category=row[1].lower())
            )
            if created:
                new_keyword.save()