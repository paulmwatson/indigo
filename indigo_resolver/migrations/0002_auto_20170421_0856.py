# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-21 08:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_resolver', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorityreference',
            name='url',
            field=models.URLField(help_text='URL from which this document can be retrieved', max_length=1024),
        ),
    ]
