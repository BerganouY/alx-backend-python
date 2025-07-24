# chats/permissions.py
from rest_framework import permissions


class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to only allow participants of a conversation to:
    - View (GET) the conversation/messages
    - Send (POST) messages to the conversation
    - Update (PUT/PATCH) their own messages
    - Delete (DELETE) their own messages
    """

    def has_object_permission(self, request, view, obj):
        # Allow GET requests for participants
        if request.method == 'GET':
            return request.user in obj.participants.all() if hasattr(obj, 'participants') else (
                request.user in obj.conversation.participants.all() if hasattr(obj, 'conversation') else False
            )

        # For Message objects
        if hasattr(obj, 'conversation'):
            # Allow POST (handled by has_permission)
            if request.method == 'POST':
                return True

            # Allow PUT/PATCH/DELETE only for the message sender
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                return obj.sender == request.user

            # Allow other methods only for participants
            return request.user in obj.conversation.participants.all()

        # For Conversation objects
        if hasattr(obj, 'participants'):
            # Allow PUT/PATCH/DELETE only if user is participant
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                return request.user in obj.participants.all()

            return True

        return False

    def has_permission(self, request, view):
        # Allow only authenticated users
        if not request.user or not request.user.is_authenticated:
            return False

        # For POST requests to messages or conversations
        if request.method == 'POST':
            # For message creation, check conversation participation
            if view.basename == 'messages':
                conversation_id = request.data.get('conversation')
                if conversation_id:
                    from .models import Conversation
                    try:
                        conversation = Conversation.objects.get(pk=conversation_id)
                        return request.user in conversation.participants.all()
                    except Conversation.DoesNotExist:
                        return False

            # For conversation creation, check if user is in participant_ids
            elif view.basename == 'conversations':
                participant_ids = request.data.get('participant_ids', [])
                if str(request.user.user_id) not in [str(pid) for pid in participant_ids]:
                    return False

        return True