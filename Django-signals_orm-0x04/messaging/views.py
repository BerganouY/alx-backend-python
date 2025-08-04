from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from .models import Message, Conversation, User
from .serializers import MessageSerializer


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation')
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )

        # Automatically set the sender to current user
        serializer.save(sender=self.request.user, conversation=conversation)


class ConversationMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )

        # Optimized query with select_related and prefetch_related
        return Message.objects.filter(
            conversation=conversation
        ).select_related(
            'sender',  # Join sender user data
            'conversation'  # Join conversation data
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender')
            )  # Optimize nested replies
        ).order_by('timestamp')


class MessageReplyView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        parent_id = self.kwargs['parent_id']
        parent_message = get_object_or_404(
            Message.objects.filter(conversation__participants=self.request.user),
            id=parent_id
        )

        # Automatically set sender and conversation from parent
        serializer.save(
            sender=self.request.user,
            conversation=parent_message.conversation,
            parent_message=parent_message
        )