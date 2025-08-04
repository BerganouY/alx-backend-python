from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Message, Conversation
from .serializers import MessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation')
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # Verify sender is in conversation participants
        if self.request.user not in conversation.participants.all():
            return Response(
                {"error": "You are not a participant in this conversation"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(
            sender=self.request.user,
            conversation=conversation
        )


class ConversationMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # Verify user is in conversation participants
        if self.request.user not in conversation.participants.all():
            return Message.objects.none()

        return Message.objects.filter(
            conversation=conversation
        ).select_related(
            'sender',
            'parent_message'
        ).prefetch_related(
            'replies'
        ).order_by('timestamp')


class MessageReplyView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        parent_id = self.kwargs['parent_id']
        parent_message = get_object_or_404(Message, id=parent_id)
        conversation = parent_message.conversation

        # Verify sender is in conversation participants
        if self.request.user not in conversation.participants.all():
            return Response(
                {"error": "You are not a participant in this conversation"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(
            sender=self.request.user,
            conversation=conversation,
            parent_message=parent_message
        )