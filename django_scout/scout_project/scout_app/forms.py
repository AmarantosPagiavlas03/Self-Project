# filepath: /c:/Users/amara/Documents/Python/self_project/django_scout/scout_project/scout_app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, PlayerProfile, Comment

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role', 'password1', 'password2')


class PlayerProfileForm(forms.ModelForm):
    class Meta:
        model = PlayerProfile
        fields = ['first_name', 'last_name', 'position', 'age', 'height', 'weight', 'agility', 'power', 'speed', 'bio', 'video_links', 'looking_for_team']

class CommentCreateForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'content': '',
        }