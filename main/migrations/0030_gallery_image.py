# Generated by Django 4.1.1 on 2022-11-18 22:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_alter_culture_options_alter_culture_lower_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='Title')),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='gallery_upload/', verbose_name='Image')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='Title')),
                ('alt', models.TextField(blank=True, null=True, verbose_name='Alt text')),
                ('gallery', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.gallery')),
            ],
        ),
    ]