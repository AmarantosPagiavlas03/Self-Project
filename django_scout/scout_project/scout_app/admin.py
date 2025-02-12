from django.contrib import admin
from .models import CustomUser, PlayerProfile, TeamProfile, PlayerStatistics

# Register CustomUser model with custom admin settings
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
    list_filter = ('role',)
    search_fields = ('username', 'email')

# Register other models
admin.site.register(PlayerProfile)
admin.site.register(PlayerStatistics)
admin.site.register(TeamProfile)