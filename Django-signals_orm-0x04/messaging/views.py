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

        # Infer receiver as the other participant
        receiver = conversation.participants.exclude(id=self.request.user.id).first()

        serializer.save(
            sender=self.request.user,
            receiver=receiver,
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

        return Message.objects.filter(
            conversation=conversation
        ).select_related(
            'sender', 'receiver', 'conversation'
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender', 'receiver')
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

        # Infer receiver: replying to sender of parent message
        receiver = parent_message.sender

        serializer.save(
            sender=self.request.user,
            receiver=receiver,
            conversation=parent_message.conversation,
            parent_message=parent_message
        )
