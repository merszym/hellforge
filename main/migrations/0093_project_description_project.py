# Generated by Django 4.1 on 2023-08-31 09:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0092_alter_author_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, max_length=200, null=True, verbose_name="name"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="description",
            name="project",
            field=models.ManyToManyField(
                related_name="description", to="main.project", verbose_name="project"
            ),
        ),
    ]