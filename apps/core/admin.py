from django.contrib import admin
from .models import City, Area, Language, ServiceRequest, Notification, ChatMessage


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'state')
    search_fields = ('name', 'state')
    list_filter = ('state',)


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'pincode')
    search_fields = ('name', 'city__name', 'pincode')
    list_filter = ('city',)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'native_name')
    search_fields = ('name', 'native_name')


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'subject', 'category', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('ticket_id', 'subject', 'description', 'user__username', 'user__email')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Ticket Info', {
            'fields': ('ticket_id', 'user', 'status')
        }),
        ('Details', {
            'fields': ('subject', 'description', 'category', 'priority')
        }),
        ('Resolution', {
            'fields': ('admin_notes',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('user', 'created_at')
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Notifications are auto-generated


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('booking', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('booking__booking_id', 'sender__username', 'message')
    readonly_fields = ('booking', 'sender', 'created_at', 'message')
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Messages are created through the chat interface
    
    def has_delete_permission(self, request, obj=None):
        return False  # Maintain chat history integrity
