# Generated by Django 3.0.7 on 2020-08-06 14:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leagues", "0004_auto_20200806_1650"),
    ]

    operations = [
        migrations.AlterField(
            model_name="player",
            name="depth_chart_position",
            field=models.CharField(max_length=50, null=True),
        ),
    ]
