from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.conf import settings
import uuid
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
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
 
    username = None
 
    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_permissions", blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

class PlayerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    position = models.CharField(max_length=20, choices=[('Goalkeeper', 'Goalkeeper'), ('Defender', 'Defender'),
                                                         ('Midfielder', 'Midfielder'), ('Forward', 'Forward')])
    team = models.ForeignKey('TeamProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
    joined_team_date = models.DateField(null=True, blank=True)
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

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # Update looking_for_team based on team status
        if self.team:
            self.looking_for_team = False
        super().save(*args, **kwargs)

class TeamProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    team_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    founded_year = models.IntegerField()
    coach_name = models.CharField(max_length=100)
    team_logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    home_stadium = models.CharField(max_length=100, null=True, blank=True)
    team_colors = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.team_name

    @property
    def roster_size(self):
        return self.players.count()

class ChatMessage(models.Model):
    sender = models.ForeignKey(CustomUser, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='posts', on_delete=models.CASCADE)
    comment_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    photo = models.ImageField(upload_to='post_photos/', blank=True, null=True)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True)

class Comment(models.Model):
    # id = models.CharField(max_length=100, default = uuid.uuid4,unique=True , editable = False, primary_key=True)
    parent_post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(CustomUser, related_name='comments', on_delete=models.CASCADE)
    content = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        try:
            return f'{self.author.username} : {self.content[:30]}'
        except:
            return f'No Author : {self.content[:30]}'

class MatchStatistics(models.Model):
    player = models.ForeignKey('PlayerProfile', on_delete=models.CASCADE, related_name='match_statistics')
    match_date = models.DateField()
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    tackles = models.IntegerField(default=0)
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['match_date']
        
    def __str__(self):
        return f"{self.player.user.username}'s stats on {self.match_date}"