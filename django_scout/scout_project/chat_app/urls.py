from django.urls import path
from .views import * 

urlpatterns = [
    path("", chat_view, name='chat_view'),
]  