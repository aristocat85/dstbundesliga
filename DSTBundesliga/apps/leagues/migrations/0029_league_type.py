# Generated by Django 3.1 on 2021-07-21 19:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leagues", "0028_delete_news"),
    ]

    operations = [
        migrations.AddField(
            model_name="league",
            name="type",
            field=models.IntegerField(
                choices=[(1, "Bundesliga"), (2, "Champions League"), (3, "Hörerliga")],
                default=1,
            ),
        ),
    ]
