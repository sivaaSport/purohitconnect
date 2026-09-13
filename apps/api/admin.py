from django.contrib import admin
from .models import MobileAuthToken


@admin.register(MobileAuthToken)
class MobileAuthTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'last_used_at', 'user_agent')
    search_fields = ('user__username', 'user__phone', 'key')
    readonly_fields = ('key', 'created_at', 'last_used_at')
