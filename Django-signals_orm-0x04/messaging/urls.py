from django.urls import path
from .views import (
    MessageCreateView,
    ConversationMessagesView,
    MessageReplyView,
    UnreadMessagesView,
    unread_messages_count,
    DeleteUserView
)

urlpatterns = [
    path('messages/', MessageCreateView.as_view(), name='message-create'),
    path('conversations/<int:conversation_id>/messages/',
         ConversationMessagesView.as_view(),
         name='conversation-messages'),
    path('messages/<int:parent_id>/reply/',
         MessageReplyView.as_view(),
         name='message-reply'),
    path('messages/unread/',
         UnreadMessagesView.as_view(),
         name='unread-messages'),
    path('messages/unread/count/',
         unread_messages_count,
         name='unread-count'),
    path('users/delete/',
         DeleteUserView.as_view(),
         name='delete-user'),
]