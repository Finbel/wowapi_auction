# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-12-27 15:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wowapi_app', '0006_lasttime'),
    ]

    operations = [
        migrations.AddField(
            model_name='auction_history',
            name='quantity',
            field=models.IntegerField(default=-1),
        ),
    ]
