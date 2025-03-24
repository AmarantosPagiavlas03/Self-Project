from django.contrib.auth.models import AbstractUser
from django.db import models


def upload_thumbnail(instance, filename):
	path = f'thumbnails/{instance.username}'
	extension = filename.split('.')[-1]
	if extension:
		path = path + '.' + extension
	return path


def upload_post_image(instance, filename):
	path = f'posts/{instance.user.username}/{filename}'
	return path


class User(AbstractUser):
	thumbnail = models.ImageField(
		upload_to=upload_thumbnail,
		null=True,
		blank=True
	)


class Post(models.Model):
	user = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
	image = models.ImageField(upload_to=upload_post_image)
	caption = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

	def __str__(self):
		return f"{self.user.username}'s post"


class Comment(models.Model):
	post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
	user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.user.username}'s comment on {self.post.user.username}'s post"


class Connection(models.Model):
	sender = models.ForeignKey(
		User,
		related_name='sent_connections',
		on_delete=models.CASCADE
	)
	receiver = models.ForeignKey(
		User,
		related_name='received_connections',
		on_delete=models.CASCADE
	)
	accepted = models.BooleanField(default=False)
	updated = models.DateTimeField(auto_now=True)
	created = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.sender.username + ' -> ' + self.receiver.username


class Message(models.Model):
	connection = models.ForeignKey(
		Connection,
		related_name='messages',
		on_delete=models.CASCADE
	)
	user = models.ForeignKey(
		User,
		related_name='my_messages',
		on_delete=models.CASCADE
	)
	text = models.TextField()
	created = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.user.username + ': ' + self.text