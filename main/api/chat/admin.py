from django.contrib import admin
from .models import User, Connection, Message, Post, Comment

admin.site.register(User)
admin.site.register(Connection)
admin.site.register(Message)
admin.site.register(Post)
admin.site.register(Comment)