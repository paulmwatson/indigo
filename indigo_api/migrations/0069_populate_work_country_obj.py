# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-23 19:14
from django.db import migrations
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text
from reversion.models import Version
import json


def populate_country_obj(apps, schema_editor):
    Work = apps.get_model("indigo_api", "Work")
    Country = apps.get_model("indigo_api", "Country")
    db_alias = schema_editor.connection.alias

    countries = {c.country.iso.lower(): c for c in Country.objects.using(db_alias).all()}

    for work in Work.objects.using(db_alias).all():
        # if this raises a key error, use the admin interface to create
        # a Country object for the missing country
        work.country_obj = countries[work.country.lower()]
        work.save(update_fields=['country_obj'])

    # Now convert reversion versions for works to store country as a foreign key,
    # not as a string.
    # We need to do this while Work.country is still a string, otherwise `version.object_version`
    # breaks when it tries to handle "za" as a foreign key.
    ct = ContentType.objects.get_for_model(Work)

    for version in Version.objects.filter(content_type=ct.pk).using(db_alias).all():
        data = json.loads(force_text(version.serialized_data.encode('utf8')))

        # change country code to a foreign key
        data[0]['fields']['country'] = countries[data[0]['fields']['country']].pk

        version.serialized_data = json.dumps(data).decode('utf8')
        version.save()


def revert_country_obj(apps, schema_editor):
    Work = apps.get_model("indigo_api", "Work")
    db_alias = schema_editor.connection.alias

    for work in Work.objects.using(db_alias).all():
        work.country = work.country_obj.country.iso.lower()
        work.save(update_fields=['country'])

    Country = apps.get_model("indigo_api", "Country")
    countries = {c.id: c for c in Country.objects.using(db_alias).all()}

    # Now revert Work versions so that country is a string, not a foreign key relation.
    ct = ContentType.objects.get_for_model(Work)
    for version in Version.objects.filter(content_type=ct.pk).using(db_alias).all():
        data = json.loads(force_text(version.serialized_data.encode('utf8')))

        # change country foreign key object to a code
        data[0]['fields']['country'] = countries[data[0]['fields']['country']].country.iso.lower()

        version.serialized_data = json.dumps(data).decode('utf8')
        version.save()


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0068_work_country_obj'),
        ('reversion', '0002_auto_20141216_1509'),
    ]

    operations = [
        migrations.RunPython(populate_country_obj, revert_country_obj),
    ]
