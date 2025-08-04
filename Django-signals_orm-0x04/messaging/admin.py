from django.contrib import admin
from .models import Message, Notification, MessageHistory

# ... existing admin registrations ...

@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    list_display = ('message', 'changed_at', 'edited_by')
    list_filter = ('changed_at',)
    search_fields = ('old_content', 'message__content')
    readonly_fields = ('message', 'old_content', 'changed_at', 'edited_by')

    def has_add_permission(self, request):
        return False  # Prevent manual creation of history records