# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-06 08:06
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0084_link_places_to_works'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='task',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotation', to='indigo_api.Task'),
        ),
    ]
