# filepath: /c:/Users/amara/Documents/Python/self_project/django_scout/scout_project/scout_app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, PlayerProfile, Comment, Post

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget = forms.Select(choices=CustomUser.ROLE_CHOICES)


class PlayerProfileForm(forms.ModelForm):
    class Meta:
        model = PlayerProfile
        fields = ['first_name', 'last_name', 'position', 'age', 'height', 'weight', 'agility', 'power', 'speed', 'bio', 'video_links', 'looking_for_team', 'user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = CustomUser.objects.all()

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

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['photo', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a caption...'}),
        }
        labels = {
            'photo': 'Upload Photo',
            'description': '',
        }