# Generated by Django 3.0.7 on 2020-08-06 19:16

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0008_auto_20200806_1910'),
    ]

    operations = [
        migrations.AlterField(
            model_name='draft',
            name='draft_order',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='draft',
            name='slot_to_roster_id',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
    ]
