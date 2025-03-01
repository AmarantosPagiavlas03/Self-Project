# Generated by Django 5.1.6 on 2025-03-01 01:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scout_app', '0009_remove_post_like_count_post_like_count'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='like_count',
            new_name='likes',
        ),
        migrations.AddField(
            model_name='post',
            name='likes_count',
            field=models.IntegerField(default=0),
        ),
    ]
