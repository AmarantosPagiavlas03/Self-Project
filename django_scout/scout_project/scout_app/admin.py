from django.contrib import admin
from .models import *

# Register CustomUser model with custom admin settings
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role')
    list_filter = ('role',)
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

# Register other models
admin.site.register(PlayerProfile)
 
admin.site.register(TeamProfile)
admin.site.register(Post)
admin.site.register(Comment)

@admin.register(MatchStatistics)
class MatchStatisticsAdmin(admin.ModelAdmin):
    list_display = ('player', 'match_date', 'goals', 'assists', 'tackles')
    list_filter = ('player', 'match_date')
    search_fields = ('player__user__username',)
    date_hierarchy = 'match_date'
