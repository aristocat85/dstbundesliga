# Generated by Django 3.0.7 on 2021-05-01 17:47

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("leagues", "0027_season"),
        ("dstffbl", "0003_auto_20210501_1939"),
    ]

    operations = [
        migrations.DeleteModel(
            name="News",
        ),
    ]
