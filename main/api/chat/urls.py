from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'connections', views.ConnectionViewSet)
router.register(r'messages', views.MessageViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)

urlpatterns = [
	path('', include(router.urls)),
	path('signup/', views.SignUpView.as_view(), name='signup'),
	path('signin/', views.SignInView.as_view(), name='signin'),
]