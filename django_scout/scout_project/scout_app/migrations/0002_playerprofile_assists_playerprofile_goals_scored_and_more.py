# Generated by Django 5.1.6 on 2025-02-11 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scout_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='playerprofile',
            name='assists',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playerprofile',
            name='goals_scored',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playerprofile',
            name='matches_played',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playerprofile',
            name='tackles',
            field=models.IntegerField(default=0),
        ),
    ]
