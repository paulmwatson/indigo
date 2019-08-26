# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-13 10:57
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0080_task_fields_added'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskLabel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=30, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.CharField(blank=True, max_length=256, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='labels',
            field=models.ManyToManyField(related_name='_task_labels_+', to='indigo_api.TaskLabel'),
        ),
    ]
