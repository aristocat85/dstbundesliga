# Generated by Django 3.0.7 on 2020-07-11 10:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leagues", "0002_auto_20200711_1232"),
    ]

    operations = [
        migrations.AddField(
            model_name="league",
            name="region",
            field=models.CharField(max_length=30, null=True),
        ),
    ]
