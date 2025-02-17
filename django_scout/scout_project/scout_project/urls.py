from django.contrib import admin
from django.urls import path, include
from scout_app import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('scout_app/', include('scout_app.urls', namespace='scout_app')),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('statistics/', views.statistics, name='statistics'),
    path('chat/', include('chat_app.urls'))
]