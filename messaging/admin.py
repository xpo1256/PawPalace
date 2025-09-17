from django.contrib import admin
from .models import Message, Conversation


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for Message model"""
    
    list_display = ('sender', 'receiver', 'dog', 'subject', 'is_read', 'sent_at')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('sender__username', 'receiver__username', 'dog__name', 'subject', 'content')
    ordering = ('-sent_at',)
    readonly_fields = ('sent_at', 'read_at')
    
    fieldsets = (
        ('Message Information', {
            'fields': ('sender', 'receiver', 'dog', 'subject')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Status', {
            'fields': ('is_read', 'sent_at', 'read_at')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'receiver', 'dog')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin configuration for Conversation model"""
    
    list_display = ('id', 'dog', 'get_participants', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('dog__name', 'participants__username')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('participants',)
    
    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants.short_description = 'Participants'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('dog').prefetch_related('participants')