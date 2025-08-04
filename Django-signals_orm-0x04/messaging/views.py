from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from .models import Message, Conversation, User
from .serializers import MessageSerializer


# Recursive reply fetcher
def get_threaded_replies(message):
    replies = []
    for reply in message.replies.all().select_related('sender'):
        replies.append({
            'id': reply.id,
            'sender': reply.sender.username,
            'content': reply.content,
            'timestamp': reply.timestamp,
            'replies': get_threaded_replies(reply)
        })
    return replies


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

        request = self.request
        serializer.save(sender=request.user, receiver=receiver, conversation=conversation)


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
            conversation=conversation,
            parent_message__isnull=True
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

        receiver = parent_message.sender

        request = self.request
        serializer.save(sender=request.user, receiver=receiver, conversation=parent_message.conversation, parent_message=parent_message)


class ThreadedMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id):
        message = get_object_or_404(
            Message.objects.select_related('sender').prefetch_related('replies'),
            id=message_id,
            conversation__participants=request.user
        )

        data = {
            'id': message.id,
            'sender': message.sender.username,
            'content': message.content,
            'timestamp': message.timestamp,
            'replies': get_threaded_replies(message)
        }

        return Response(data)


class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'detail': 'User deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


delete_user = DeleteUserView.as_view()
