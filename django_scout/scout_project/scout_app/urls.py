from django.urls import path
from . import views
 
app_name = 'scout_app'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('statistics/', views.statistics, name='statistics'),
    path('statistics/detailed/', views.detailed_statistics_view, name='detailed_statistics'),
    path('search/', views.search, name='search'),
    path('player/<int:player_id>/', views.view_player_profile, name='view_player_profile'),
    path('player_dashboard/<int:player_id>/', views.view_player_dashboard, name='player_dashboard'),
    path('player_dashboard/<int:player_id>/load_more_posts/', views.load_more_posts, name='load_more_posts'),
    path('team_dashboard/<int:team_id>/', views.view_team_dashboard, name='team_dashboard'),
    path('post/<int:post_id>/', views.view_post, name='view_post'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('post/create/', views.create_post, name='create_post'),
]

