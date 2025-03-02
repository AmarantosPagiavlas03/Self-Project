from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render
from .models import PlayerProfile, TeamProfile, Post,Comment
from .forms import *
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import PlayerProfile
from .forms import PlayerProfileForm
from django.contrib import messages
from django.http import JsonResponse
import json
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

def home(request):
    if not request.user.is_authenticated:
        return redirect('scout_app:login')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Post created successfully!")
            return redirect('scout_app:home')
        else:
            messages.error(request, "Error creating post. Please check the form.")
    else:
        form = PostForm()
    
    posts = Post.objects.all().order_by('-timestamp')
    commentcreateform = CommentCreateForm()
    context = {
        'posts': posts,
        'commentcreateform': commentcreateform,
        'post_form': form
    }
    return render(request, 'home.html', context)

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

def register(request):
    logger.debug("Entering register view")
    if request.method == 'POST':
        logger.debug("Received POST request")
        logger.debug(f"POST data: {request.POST}")
        form = CustomUserCreationForm(request.POST)
        logger.debug(f"Form errors: {form.errors}")
        if form.is_valid():
            logger.debug("Form is valid")
            user = form.save()
            logger.debug(f"User created: {user}")
            # Create a PlayerProfile for the user if they are registering as a Player
            if user.role == 'Player':
                player_profile = PlayerProfile.objects.create(
                    user=user,
                    first_name=form.cleaned_data.get('first_name'),
                    last_name=form.cleaned_data.get('last_name')
                )
                logger.debug(f"PlayerProfile created: {player_profile}")
            login(request, user)
            messages.success(request, 'Registration successful!')
            logger.debug("User logged in and redirected to login page")
            return redirect('scout_app:login')
        else:
            logger.debug("Form is invalid")
            logger.debug(f"Form errors: {form.errors}")
            messages.error(request, f'Please correct the errors below.{form.errors}')
    else:
        form = CustomUserCreationForm()
        logger.debug("GET request received, rendering registration form")
    return render(request, 'register.html', {'form': form})



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
            return redirect('scout_app:player_dashboard', player_id=profile.id)
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

    context = {
        'profile': profile
    }
    return render(request, 'view_profile.html', context)

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

    # Example normalization: assume maximum possible values are known
    max_values = {
        'agility': 100,
        'power': 100,
        'speed': 100,
        'strategy': 100,
    }

    profile_data = {
        'agility': player_profile.agility,
        'power': player_profile.power,
        'speed': player_profile.speed,
        'strategy': player_profile.strategy,
    }

    # Normalize to percentage values:
    normalized_data = [
        (profile_data['agility'] / max_values['agility']) * 100 if profile_data['agility'] is not None and max_values['agility'] else 0,
        (profile_data['power'] / max_values['power']) * 100 if profile_data['power'] is not None and max_values['power'] else 0,
        (profile_data['speed'] / max_values['speed']) * 100 if profile_data['speed'] is not None and max_values['speed'] else 0,
        (profile_data['strategy'] / max_values['strategy']) * 100 if profile_data['strategy'] is not None and max_values['strategy'] else 0,
    ]

    context["performance_data"] = {
        "labels": json.dumps(['Agility', 'Power', 'Speed', 'Strategy']),
        "data": json.dumps(normalized_data)
    }
    context["bar_plot_data"] = {
        "labels": json.dumps(['Matches Played', 'Goals Scored', 'Assists', 'Tackles']),
        "data": json.dumps([player_profile.matches_played, player_profile.goals_scored, player_profile.assists, player_profile.tackles])
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
        profile = None

    if request.method == 'POST':
        user_form = CustomUserEditForm(request.POST, instance=user)
        profile_form = PlayerProfileEditForm(request.POST, instance=profile)
        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile = profile_form.save(commit=False)
                profile.age = profile_form.cleaned_data.get('age', profile.age)
                profile.height = profile_form.cleaned_data.get('height', profile.height)
                profile.weight = profile_form.cleaned_data.get('weight', profile.weight)
                profile.agility = profile_form.cleaned_data.get('agility', profile.agility)
                profile.power = profile_form.cleaned_data.get('power', profile.power)
                profile.speed = profile_form.cleaned_data.get('speed', profile.speed)
                profile.bio = profile_form.cleaned_data.get('bio', profile.bio)
                profile.video_links = profile_form.cleaned_data.get('video_links', profile.video_links)
                profile.looking_for_team = profile_form.cleaned_data.get('looking_for_team', profile.looking_for_team)
                profile.save()
                messages.success(request, "Changes saved successfully.")
                return redirect('scout_app:dashboard')
        else:
            messages.error(request, f"Error updating profile. Please check the fields.{user_form.errors}")
    return render(request, 'edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})

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


# @login_required
# def search(request):
#     if not request.user.is_authenticated:
#         return redirect('scout_app:login')
    
#     query = ''
#     players = None
    
#     if request.method == 'POST':
#         query = request.POST.get('query', '')
#         players = PlayerProfile.objects.filter(
#             Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(position__icontains=query)
#         ) if query else None

#         if players and players.count() == 1:
#             player = players.first()
#             return redirect('scout_app:player_dashboard', player_id=player.id)

#     context = {
#         'query': query,
#         'players': players
#     }
#     return render(request, 'search.html', context)

@login_required
def view_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    commentcreateform = CommentCreateForm()
    context = {
        'post': post,
        'commentcreateform': commentcreateform
    }
    return render(request, 'view_post.html', context)

@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        
        # Check if it's a JSON request
        if request.headers.get('content-type') == 'application/json':
            data = json.loads(request.body)
            form = CommentCreateForm({'content': data.get('content', '')})
        else:
            form = CommentCreateForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.parent_post = post
            comment.author = request.user
            comment.save()
            post.comment_count += 1
            post.save()
            
            # Return JSON response if it's an AJAX request
            if request.headers.get('content-type') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment': comment.content,
                    'author': comment.author.username,
                    'timestamp': comment.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'comment_count': post.comment_count
                })
            return redirect('scout_app:view_post', post_id=post.id)
        else:
            if request.headers.get('content-type') == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': dict(form.errors.items())
                })
            messages.error(request, "Error adding comment. Please try again.")
            return redirect('scout_app:view_post', post_id=post.id)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# dropdown search function
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from .models import PlayerProfile

@login_required
def search(request):
    query = request.GET.get('query', '')
    players = PlayerProfile.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(position__icontains=query)
    )

    # Check if the request is for JSON (dropdown)
    if request.headers.get('Accept') == 'application/json':
        players = players[:3]  # Limit to 3 results for dropdown
        players_data = [
            {
                'id': player.id,
                'first_name': player.first_name,
                'last_name': player.last_name,
                'position': player.position
            }
            for player in players
        ]
        return JsonResponse({'players': players_data})

    # Render the full search page
    context = {
        'query': query,
        'players': players
    }
    return render(request, 'search.html', context)

@csrf_exempt
@require_POST
def like_post(request, post_id):
    try:
        logger.info(f"Received like request for post id: {post_id}")
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        liked = data.get('liked', False)
        
        logger.info(f"Post found: {post_id}, liked: {liked}")
        
        if liked:
            post.likes.add(request.user)
            post.likes_count += 1
        else:
            post.likes.remove(request.user)
            post.likes_count -= 1
        
        post.save()
        
        logger.info(f"Post {post_id} updated successfully. New likes count: {post.likes_count}")
        
        return JsonResponse({'success': True, 'likes_count': post.likes_count})
    except Post.DoesNotExist:
        logger.error(f"Post with id {post_id} does not exist.")
        return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def delete_comment(request, comment_id):
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if the user is the author of the comment
        if comment.author != request.user:
            return JsonResponse({
                'success': False,
                'error': 'You can only delete your own comments'
            }, status=403)
        
        # Check if the comment is less than 1 hour old
        time_threshold = timezone.now() - timedelta(hours=1)
        if comment.timestamp < time_threshold:
            return JsonResponse({
                'success': False,
                'error': 'Comments can only be deleted within 1 hour of posting'
            }, status=403)
        
        # Get the parent post to update comment count
        post = comment.parent_post
        post.comment_count -= 1
        post.save()
        
        # Delete the comment
        comment.delete()
        
        return JsonResponse({
            'success': True,
            'comment_count': post.comment_count
        })
    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while deleting the comment'
        }, status=500)
