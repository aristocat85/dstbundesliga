# Generated by Django 3.0.7 on 2021-07-08 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dstffbl', '0004_seasonuser_possible_commish'),
    ]

    operations = [
        migrations.AddField(
            model_name='seasonuser',
            name='registration_ts',
            field=models.DateTimeField(auto_now=True),
        ),
    ]