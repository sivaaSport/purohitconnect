from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'reviewer', 'purohit', 'rating', 'is_verified', 'created_at')
    list_filter = ('rating', 'is_verified', 'created_at')
    search_fields = ('title', 'comment', 'reviewer__username', 'purohit__name')
    readonly_fields = ('booking',)
