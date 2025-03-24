from django.contrib.auth import authenticate
from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, SignUpSerializer
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from .models import User, Connection, Message, Post, Comment
from django.db import models
from .serializers import RequestSerializer, FriendSerializer	
from .serializers import MessageSerializer
from .serializers import PostSerializer
from .serializers import CommentSerializer
from .serializers import ConnectionSerializer
from .serializers import UserSerializer
from .serializers import SignUpSerializer



def get_auth_for_user(user):
	tokens = RefreshToken.for_user(user)
	return {
		'user': UserSerializer(user).data,
		'tokens': {
			'access': str(tokens.access_token),
			'refresh': str(tokens),
		}
	}


class SignInView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		username = request.data.get('username')
		password = request.data.get('password')
		if not username or not password:
			return Response(status=400)
		
		user = authenticate(username=username, password=password)
		if not user:
			return Response(status=401)

		user_data = get_auth_for_user(user)

		return Response(user_data)


class SignUpView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		new_user = SignUpSerializer(data=request.data)
		new_user.is_valid(raise_exception=True)
		user = new_user.save()

		user_data = get_auth_for_user(user)

		return Response(user_data)


class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		queryset = User.objects.all()
		username = self.request.query_params.get('username', None)
		if username:
			queryset = queryset.filter(username=username)
		return queryset


class ConnectionViewSet(viewsets.ModelViewSet):
	queryset = Connection.objects.all()
	serializer_class = ConnectionSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return Connection.objects.filter(
			models.Q(sender=self.request.user) |
			models.Q(receiver=self.request.user)
		)

	def perform_create(self, serializer):
		serializer.save(sender=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
	queryset = Message.objects.all()
	serializer_class = MessageSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		connection_id = self.request.query_params.get('connection', None)
		if connection_id:
			return Message.objects.filter(connection_id=connection_id)
		return Message.objects.none()

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)


class PostViewSet(viewsets.ModelViewSet):
	queryset = Post.objects.all()
	serializer_class = PostSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		queryset = Post.objects.all().order_by('-created_at')
		username = self.request.query_params.get('username', None)
		if username:
			queryset = queryset.filter(user__username=username)
		return queryset

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

	@action(detail=True, methods=['post'])
	def like(self, request, pk=None):
		post = self.get_object()
		if request.user in post.likes.all():
			post.likes.remove(request.user)
		else:
			post.likes.add(request.user)
		return Response({'status': 'success'})


class CommentViewSet(viewsets.ModelViewSet):
	queryset = Comment.objects.all()
	serializer_class = CommentSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		post_id = self.request.query_params.get('post', None)
		if post_id:
			return Comment.objects.filter(post_id=post_id).order_by('-created_at')
		return Comment.objects.none()

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)