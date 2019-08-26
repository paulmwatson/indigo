# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-03 16:33
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Authority',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Descriptive name of this resolver', max_length=255, unique=True)),
                ('url', models.URLField(help_text='Website for this authority')),
            ],
            options={
                'verbose_name_plural': 'Authorities',
            },
        ),
        migrations.CreateModel(
            name='AuthorityReference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('frbr_uri', models.CharField(db_index=True, help_text='FRBR Work or Expression URI to match on', max_length=255)),
                ('title', models.CharField(help_text='Document title', max_length=255)),
                ('url', models.URLField(help_text='URL from which this document can be retrieved', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('authority', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='references', to='indigo_resolver.Authority')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='authorityreference',
            unique_together=set([('authority', 'frbr_uri')]),
        ),
    ]
