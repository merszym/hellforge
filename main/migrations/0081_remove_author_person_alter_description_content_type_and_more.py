# Generated by Django 4.1 on 2023-08-23 13:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("main", "0080_remove_site_description_remove_site_gallery_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="author",
            name="person",
        ),
        migrations.AlterField(
            model_name="description",
            name="content_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_query_name="description",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="author",
            name="person",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="author",
                to="main.contactperson",
                verbose_name="person",
            ),
        ),
    ]
