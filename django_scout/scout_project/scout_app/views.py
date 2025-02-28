from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render
from .models import PlayerProfile, TeamProfile
from .forms import CustomUserCreationForm
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import PlayerProfile
from .forms import PlayerProfileForm
from django.contrib import messages
from django.http import JsonResponse
import json
from django.db.models import Q
from django.shortcuts import get_object_or_404

def home(request):
    if not request.user.is_authenticated:
        return redirect('scout_app:login')
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Attempt to find an existing profile to assign to this user
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            try:
                profile = PlayerProfile.objects.get(first_name=first_name, last_name=last_name, user__isnull=True)
                profile.user = user
                profile.save()
            except PlayerProfile.DoesNotExist:
                pass
            login(request, user)
            return redirect('scout_app:dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = "login.html"
    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        remember_me = self.request.POST.get("remember_me")
        if remember_me:
            self.request.session.set_expiry(1209600)  # 2 weeks
        else:
            self.request.session.set_expiry(0)  # session only
        messages.success(self.request, "Successfully logged in.")
        return redirect("scout_app:dashboard")

    def form_invalid(self, form):
        messages.error(self.request, "Incorrect username or password. Please try again.")
        return self.render_to_response(self.get_context_data(form=form))

@login_required
def logout_view(request):
    logout(request)
    return redirect("scout_app:login")

@login_required
def dashboard(request):
    
    user = request.user
    context = {"user": user}

    if user.role == 'Player':
        try:
            profile = PlayerProfile.objects.get(user=user)
            # Example normalization: assume maximum possible values are known
            max_values = {
                'agility': 100,
                'power': 100,
                'speed': 100,
                'strategy': 100,
            }

            profile_data = {
                'agility': profile.agility,
                'power': profile.power,
                'speed': profile.speed,
                'strategy': profile.strategy,
            }

            # Normalize to percentage values:
            normalized_data = [
                (profile_data['agility'] / max_values['agility']) * 100 if max_values['agility'] else 0,
                (profile_data['power'] / max_values['power']) * 100 if max_values['power'] else 0,
                (profile_data['speed'] / max_values['speed']) * 100 if max_values['speed'] else 0,
                (profile_data['strategy'] / max_values['strategy']) * 100 if max_values['strategy'] else 0,
            ]

            context["performance_data"] = {
                "labels": json.dumps(['Agility', 'Power', 'Speed', 'Strategy']),
                "data": json.dumps(normalized_data)
            }
            context["bar_plot_data"] = {
                "labels": json.dumps(['Matches Played', 'Goals Scored', 'Assists', 'Tackles']),
                "data": json.dumps([profile.matches_played, profile.goals_scored, profile.assists, profile.tackles])
            }

            return render(request, "player_dashboard.html", context)
        except PlayerProfile.DoesNotExist:
            pass
    elif user.role == 'Team':
        try:
            profile = TeamProfile.objects.get(user=user)
            context["profile"] = profile
            # context["team_stats"] = profile.get_team_stats()  # Example additional data
            return render(request, "team_dashboard.html", context)
        except TeamProfile.DoesNotExist:
            pass

    context["general_info"] = "Welcome to your dashboard!"  # Example additional data
    return render(request, "dashboard.html", context)

@login_required
def view_profile(request):
    user = request.user
    try:
        profile = PlayerProfile.objects.get(user=user)
    except PlayerProfile.DoesNotExist:
        profile = None

@login_required
def view_player_profile(request, player_id):
    player_profile = get_object_or_404(PlayerProfile, id=player_id)
    context = {
        'profile': player_profile
    }
    return render(request, 'view_profile.html', context)
    
@login_required
def view_player_dashboard(request, player_id):
    player_profile = get_object_or_404(PlayerProfile, id=player_id)
    context = {
        'profile': player_profile,
        'performance_data': {
            'labels': ['Agility', 'Power', 'Speed', 'Strategy'],
            'data': [
                player_profile.agility,
                player_profile.power,
                player_profile.speed,
                player_profile.strategy
            ]
        },
        'bar_plot_data': {
            'labels': ['Matches Played', 'Goals Scored', 'Assists', 'Tackles'],
            'data': [
                player_profile.matches_played,
                player_profile.goals_scored,
                player_profile.assists,
                player_profile.tackles
            ]
        }
    }
    return render(request, 'player_dashboard.html', context)

@login_required
def edit_profile(request):
    user = request.user
    try:
        if user.role == 'Player':
            profile = PlayerProfile.objects.get(user=user)
        else:
            profile = None
    except PlayerProfile.DoesNotExist:
        pass

    if request.method == 'POST' and require_POST(request.path):
        form = PlayerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Changes saved successfully.")
            return redirect('scout_app:dashboard')
        else:
            messages.error(request, "Error updating profile. Please check the fields.")
            return render(request, 'edit_profile.html', {'form': form})
    else:
        if profile:
            form = PlayerProfileForm(instance=profile)
            return render(request, 'edit_profile.html', {'form': form})
        else:
            return render(request, 'edit_profile.html', {'message': "No profile found."})


@login_required
def statistics(request):
    statistics = {
        "matches_played": 25,
        "goals_scored": 10,
        "assists": 7,
        "yellow_cards": 3,
        "red_cards": 1,
    }
    
    return render(request, "statistics.html", {"statistics": statistics})


@login_required
def search(request):
    if not request.user.is_authenticated:
        return redirect('scout_app:login')
    
    query = ''
    players = None
    
    if request.method == 'POST':
        query = request.POST.get('query', '')
        players = PlayerProfile.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(position__icontains=query)
        ) if query else None

        if players and players.count() == 1:
            player = players.first()
            return redirect('scout_app:player_dashboard', player_id=player.id)

    context = {
        'query': query,
        'players': players
    }
    return render(request, 'search.html', context)