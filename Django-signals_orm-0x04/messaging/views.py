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
        receiver_id = self.request.data.get('receiver')

        # Get or create conversation
        if conversation_id:
            conversation = get_object_or_404(
                Conversation.objects.filter(participants=self.request.user),
                id=conversation_id
            )
        else:
            # Create new conversation if needed
            receiver = get_object_or_404(User, id=receiver_id)
            conversation = Conversation.objects.create()
            conversation.participants.add(self.request.user, receiver)

        # Explicitly set both sender and receiver
        serializer.save(
            sender=self.request.user,
            receiver=receiver if not conversation_id else None,
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

        # Optimized query with sender, receiver, and replies
        return Message.objects.filter(
            conversation=conversation
        ).select_related(
            'sender',  # Optimize sender lookups
            'receiver',  # Optimize receiver lookups
            'conversation'  # Optimize conversation lookups
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender', 'receiver')
            )  # Optimize nested replies
        ).order_by('timestamp')


class MessageDetailView(generics.RetrieveAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related(
            'sender',
            'receiver',
            'conversation',
            'parent_message'
        )