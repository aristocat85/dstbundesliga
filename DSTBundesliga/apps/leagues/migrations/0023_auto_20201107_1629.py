# Generated by Django 3.0.7 on 2020-11-07 15:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("leagues", "0022_auto_20201028_1936"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pick",
            name="player",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="picks",
                to="leagues.Player",
            ),
        ),
    ]
