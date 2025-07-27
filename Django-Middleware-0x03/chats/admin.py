from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Conversation, Message


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'created_at')
    list_filter = ('role', 'created_at', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'role')
        }),
    )


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('conversation_id', 'created_at', 'get_participants')
    list_filter = ('created_at',)
    search_fields = ('participants__email', 'participants__first_name')

    def get_participants(self, obj):
        return ", ".join([str(user) for user in obj.participants.all()])

    get_participants.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'sender', 'conversation', 'sent_at', 'message_preview')
    list_filter = ('sent_at', 'sender')
    search_fields = ('message_body', 'sender__email')

    def message_preview(self, obj):
        return obj.message_body[:50] + "..." if len(obj.message_body) > 50 else obj.message_body

    message_preview.short_description = 'Preview'