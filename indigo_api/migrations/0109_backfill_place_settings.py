# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-08-15 14:09
from django.db import migrations


def populate_settings(apps, schema_editor):
    PlaceSettings = apps.get_model("indigo_api", "PlaceSettings")
    Country = apps.get_model("indigo_api", "Country")
    Locality = apps.get_model("indigo_api", "Locality")
    db_alias = schema_editor.connection.alias

    for country in Country.objects.all():
        PlaceSettings(country=country).save(using=db_alias)

    for locality in Locality.objects.all():
        PlaceSettings(country=locality.country, locality=locality).save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0108_place_settings'),
    ]

    operations = [
        migrations.RunPython(populate_settings, migrations.RunPython.noop),
    ]
