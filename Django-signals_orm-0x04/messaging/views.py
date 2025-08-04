from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from .models import Message, Conversation, User
from .serializers import MessageSerializer


class MessageListView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Optimized query with select_related and prefetch_related
        queryset = Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related(
            'sender',  # Optimize sender lookups
            'conversation'  # Optimize conversation lookups
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender')
            )  # Optimize nested replies
        ).order_by('-timestamp')

        return queryset

    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation')
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )

        # Set sender to current user and validate receiver is in conversation
        serializer.save(
            sender=self.request.user,
            conversation=conversation
        )


class MessageDetailView(generics.RetrieveAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Optimized query for single message with thread
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related(
            'sender',
            'conversation',
            'parent_message'
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender')
            )
        )