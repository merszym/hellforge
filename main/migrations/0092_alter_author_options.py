# Generated by Django 4.1 on 2023-08-28 14:08

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0091_remove_author_order_author_position_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="author",
            options={"ordering": ["position"]},
        ),
    ]