# Generated by Django 3.2.13 on 2023-12-07 10:14
from django.db import migrations


def backfill_work_in_progress(apps, schema_editor):
    """ Mark existing works as work_in_progress = False; only new ones should be True by default.
    """
    Work = apps.get_model('indigo_api', 'Work')
    db_alias = schema_editor.connection.alias

    for work in Work.objects.using(db_alias).iterator(100):
        work.work_in_progress = False
        work.save()


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0029_work_in_progress'),
    ]

    operations = [
        migrations.RunPython(backfill_work_in_progress, migrations.RunPython.noop)
    ]
