from django.db import models
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.contrib.auth.models import AbstractUser

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


    groups = models.ManyToManyField(
        Group,
        related_name="customuser_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions",
        blank=True
    )

    image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField(max_length=50,null=True, blank=True)  # Display name field
    phone_number = models.CharField(max_length=20,null=True, blank=True)  # Phone number field
    birth_date = models.DateField(null=True, blank=True)  # Birth date field

    def __str__(self):
        return f"{self.displayname} ({self.role})"

    # def is_anonymous(self):
    #     return self.session_key == str(self.id)

    # @property
    # def is_authenticated(self):
    #     # Implement custom logic here
    #     return super().is_authenticated()

    @property
    def name(self):
        if self.displayname:
            return self.displayname
        return self.user.username

    @property
    def avatar(self):
        if self.image:
            return self.image.url
        return f'{settings.STATIC_URL}images/avatar.svg'

 


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

    # Added is_editable field for admin access only
    is_editable = models.BooleanField(default=False)

class TeamProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    team_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    founded_year = models.IntegerField()
    coach_name = models.CharField(max_length=100)

    # Added league and division fields
    league = models.CharField(max_length=50,null=True, blank=True)
    division = models.CharField(max_length=50,null=True, blank=True)

class ChatMessage(models.Model):
    sender = models.ForeignKey(CustomUser, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField(max_length=500)  # Added max_length for better performance
    timestamp = models.DateTimeField(auto_now_add=True)

class ChatGroup(models.Model):
    group_name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.group_name

class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, related_name='chat_messages', on_delete=models.CASCADE)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    body = models.TextField(max_length=300)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author.username} : {self.body}'

    class Meta:
        ordering = ['-created']