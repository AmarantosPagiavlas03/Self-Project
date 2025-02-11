from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

# Custom User Model
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('Player', 'Player'), 
        ('Scout', 'Scout'), 
        ('Team', 'Team'), 
        ('Admin', 'Admin')
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Player')
    email = models.EmailField(unique=True)

    # Fix conflicts with Django’s default User model
    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_permissions", blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class PlayerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    position = models.CharField(max_length=20, choices=[('Goalkeeper', 'Goalkeeper'), ('Defender', 'Defender'),
                                                         ('Midfielder', 'Midfielder'), ('Forward', 'Forward')])
    age = models.IntegerField()
    height = models.IntegerField()
    weight = models.IntegerField()
    agility = models.IntegerField()
    power = models.IntegerField()
    speed = models.IntegerField()
    strategy = models.IntegerField()

    bio = models.TextField()
    video_links = models.TextField(blank=True, null=True)
    looking_for_team = models.BooleanField(default=True)
    matches_played = models.IntegerField(default=0)
    goals_scored = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    tackles = models.IntegerField(default=0)

class TeamProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    team_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    founded_year = models.IntegerField()
    coach_name = models.CharField(max_length=100)

class ChatMessage(models.Model):
    sender = models.ForeignKey(CustomUser, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
