from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from .models import Message, Conversation
from .serializers import MessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation')
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )

        # Explicitly set the sender to the current user
        serializer.save(
            sender=self.request.user,  # This is the key line that was missing
            conversation=conversation
        )


class ConversationMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )

        # Optimized query using select_related and prefetch_related
        return Message.objects.filter(
            conversation=conversation
        ).select_related(
            'sender',  # Optimizes sender lookups
            'conversation',  # Optimizes conversation lookups
            'parent_message__sender'  # Optimizes parent message sender lookups
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender')
                .prefetch_related(
                    Prefetch(
                        'replies',
                        queryset=Message.objects.select_related('sender')
                    )
                )
            )
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

        # Explicitly set the sender to the current user
        serializer.save(
            sender=self.request.user,  # This is the key line that was missing
            conversation=parent_message.conversation,
            parent_message=parent_message
        )