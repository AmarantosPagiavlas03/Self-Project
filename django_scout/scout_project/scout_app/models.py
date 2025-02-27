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
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    position = models.CharField(max_length=20, choices=[('Goalkeeper', 'Goalkeeper'), ('Defender', 'Defender'),
                                                         ('Midfielder', 'Midfielder'), ('Forward', 'Forward')])
    age = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    agility = models.IntegerField(null=True, blank=True)
    power = models.IntegerField(null=True, blank=True)
    speed = models.IntegerField(null=True, blank=True)
    strategy = models.IntegerField(null=True, blank=True)

    bio = models.TextField(null=True, blank=True)
    video_links = models.TextField(blank=True, null=True)
    looking_for_team = models.BooleanField(default=True)
    matches_played = models.IntegerField(default=0)
    goals_scored = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    tackles = models.IntegerField(default=0)

class PlayerStatistics(models.Model):
    player_profile = models.ForeignKey(PlayerProfile, related_name='statistics', on_delete=models.CASCADE)
    season = models.CharField(max_length=10)
    
    # Main stats
    goals = models.IntegerField(default=0)
    own_goals = models.IntegerField(default=0)
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)
    minutes_played = models.CharField(max_length=10)  # Store as string with '
    
    # Additional stats
    goal_every = models.CharField(max_length=10, default='--')
    own_goal_every = models.CharField(max_length=10, default='--')
    yellow_card_every = models.CharField(max_length=10, default='--')
    red_card_every = models.CharField(max_length=10, default='--')
    
    class Meta:
        unique_together = ('player_profile', 'season')
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
