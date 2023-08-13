# Generated by Django 3.1 on 2021-07-25 07:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("leagues", "0029_league_type"),
        ("dstffbl", "0006_seasonuser_last_years_league"),
    ]

    operations = [
        migrations.AddField(
            model_name="seasonuser",
            name="dst_player",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="leagues.dstplayer",
            ),
        ),
    ]
