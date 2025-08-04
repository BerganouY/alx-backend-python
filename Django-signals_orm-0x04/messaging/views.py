from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from django.views.decorators.cache import cache_page
from rest_framework.decorators import api_view, permission_classes
from .models import Message, Conversation, User
from .serializers import MessageSerializer

# Custom manager usage example
class UnreadMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.unread.for_user(self.request.user)

# Cached conversation messages view
class ConversationMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    @cache_page(60)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )
        return Message.objects.filter(
            conversation=conversation
        ).select_related('sender', 'receiver')

class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation')
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )
        receiver = conversation.participants.exclude(id=self.request.user.id).first()
        serializer.save(sender=self.request.user, receiver=receiver, conversation=conversation)

class MessageReplyView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        parent_id = self.kwargs['parent_id']
        parent_message = get_object_or_404(
            Message.objects.filter(conversation__participants=self.request.user),
            id=parent_id
        )

        receiver = parent_message.sender

        request = self.request
        serializer.save(sender=request.user, receiver=receiver, conversation=parent_message.conversation, parent_message=parent_message)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60)
def unread_messages_count(request):
    count = Message.unread.for_user(request.user).count()
    return Response({'unread_count': count})

class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'detail': 'User deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)