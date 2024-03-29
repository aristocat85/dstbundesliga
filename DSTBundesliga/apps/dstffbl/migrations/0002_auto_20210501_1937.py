# Generated by Django 3.0.7 on 2021-05-01 17:37

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):
    dependencies = [
        ("dstffbl", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Announcement",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("valid_from", models.DateField()),
                ("valid_to", models.DateField()),
                ("content", tinymce.models.HTMLField()),
            ],
            options={
                "verbose_name_plural": "Announcements",
            },
        ),
        migrations.CreateModel(
            name="News",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.TextField()),
                ("content", tinymce.models.HTMLField()),
                ("image", models.CharField(default="dst_logo_96.png", max_length=255)),
                ("date", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "News",
            },
        ),
        migrations.AlterField(
            model_name="seasonuser",
            name="region",
            field=models.IntegerField(
                choices=[
                    (
                        1,
                        "Nord (Niedersachsen, Bremen, Hamburg, Mecklenburg-Vorpommern , Schleswig-Holstein)",
                    ),
                    (
                        2,
                        "Ost (Thüringen, Berlin, Sachsen, Sachsen-Anhalt, Brandenburg)",
                    ),
                    (3, "Süd (Bayern, Baden-Württemberg)"),
                    (
                        4,
                        "West (Nordrhein-Westfalen, Hessen, Saarland, Rheinland-Pfalz)",
                    ),
                    (5, "Ausland"),
                ]
            ),
        ),
    ]
