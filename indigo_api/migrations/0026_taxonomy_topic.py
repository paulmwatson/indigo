# Generated by Django 3.2.13 on 2023-07-17 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0025_remove_country_publication_date_optional'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxonomyTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=255, unique=True)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('name', models.CharField(max_length=512)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'verbose_name': 'taxonomy topic',
                'verbose_name_plural': 'taxonomy topics',
            },
        ),
        migrations.AddField(
            model_name='work',
            name='taxonomy_topics',
            field=models.ManyToManyField(related_name='works', to='indigo_api.TaxonomyTopic'),
        ),
    ]
