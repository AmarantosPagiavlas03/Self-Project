# Generated by Django 5.1.6 on 2025-02-12 13:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scout_app', '0004_alter_playerprofile_age_alter_playerprofile_agility_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playerprofile',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
