# Generated by Django 4.1 on 2024-03-28 15:07

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0126_faunalanalysis_faunalresults_remove_foundtaxon_taxon_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="faunalanalysis",
            unique_together={("layer", "ref")},
        ),
    ]