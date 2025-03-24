from rest_framework import serializers
from .models import User, Connection, Message, Post, Comment



class SignUpSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = [
			'username',
			'first_name',
			'last_name',
			'password'
		]
		extra_kwargs = {
			'password': {
				# Ensures that when serializing, this field will be excluded
				'write_only': True
			}
		}

	def create(self, validated_data):
		# Clean all values, set as lowercase
		username   = validated_data['username'].lower()
		first_name = validated_data['first_name'].lower()
		last_name  = validated_data['last_name'].lower()
		# Create new user
		user = User.objects.create(
			username=username,
			first_name=first_name,
			last_name=last_name
		)
		password = validated_data['password']
		user.set_password(password)
		user.save()
		return user


class UserSerializer(serializers.ModelSerializer):
	name = serializers.SerializerMethodField()

	class Meta:
		model = User
		fields = ('id', 'username', 'email', 'thumbnail', 'name')
		read_only_fields = ('id',)

	def get_name(self, obj):
		fname = obj.first_name.capitalize()
		lname = obj.last_name.capitalize()
		return fname + ' ' + lname


class SearchSerializer(UserSerializer):
	status = serializers.SerializerMethodField()

	class Meta:
		model = User
		fields = [
			'username',
			'name',
			'thumbnail',
			'status'
		]
	
	def get_status(self, obj):
		if obj.pending_them:
			return 'pending-them'
		elif obj.pending_me:
			return 'pending-me'
		elif obj.connected:
			return 'connected'
		return 'no-connection'


class RequestSerializer(serializers.ModelSerializer):
	sender = UserSerializer()
	receiver = UserSerializer()

	class Meta:
		model = Connection
		fields = [
			'id',
			'sender',
			'receiver',
			'created'
		]


class FriendSerializer(serializers.ModelSerializer):
	friend = serializers.SerializerMethodField()
	preview = serializers.SerializerMethodField()
	updated = serializers.SerializerMethodField()
	
	class Meta:
		model = Connection
		fields = [
			'id',
			'friend',
			'preview',
			'updated'
		]

	def get_friend(self, obj):
		# If Im the sender
		if self.context['user'] == obj.sender:
			return UserSerializer(obj.receiver).data
		# If Im the receiver
		elif self.context['user'] == obj.receiver:
			return UserSerializer(obj.sender).data
		else:
			print('Error: No user found in friendserializer')

	def get_preview(self, obj):
		default = 'New connection'
		if not hasattr(obj, 'latest_text'):
			return default
		return obj.latest_text or default

	def get_updated(self, obj):
		if not hasattr(obj, 'latest_created'):
			date = obj.updated
		else:
			date = obj.latest_created or obj.updated
		return date.isoformat()


class CommentSerializer(serializers.ModelSerializer):
	user = UserSerializer(read_only=True)

	class Meta:
		model = Comment
		fields = ('id', 'user', 'text', 'created_at')
		read_only_fields = ('id', 'created_at')


class PostSerializer(serializers.ModelSerializer):
	user = UserSerializer(read_only=True)
	comments = CommentSerializer(many=True, read_only=True)
	likes_count = serializers.SerializerMethodField()

	class Meta:
		model = Post
		fields = ('id', 'user', 'image', 'caption', 'created_at', 'comments', 'likes_count')
		read_only_fields = ('id', 'created_at')

	def get_likes_count(self, obj):
		return obj.likes.count()


class ConnectionSerializer(serializers.ModelSerializer):
	sender = UserSerializer(read_only=True)
	receiver = UserSerializer(read_only=True)

	class Meta:
		model = Connection
		fields = ('id', 'sender', 'receiver', 'accepted', 'updated', 'created')
		read_only_fields = ('id', 'updated', 'created')


class MessageSerializer(serializers.ModelSerializer):
	user = UserSerializer(read_only=True)

	class Meta:
		model = Message
		fields = ('id', 'connection', 'user', 'text', 'created')
		read_only_fields = ('id', 'created')