from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import User, Conversation, Message
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer

    def get_queryset(self):
        """Filter conversations to show only those the user participates in"""
        user = self.request.user
        if user.is_authenticated:
            return Conversation.objects.filter(participants=user)
        return Conversation.objects.none()

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to a specific conversation"""
        conversation = self.get_object()

        # Check if user is participant in conversation
        if request.user not in conversation.participants.all():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                sender=request.user,
                conversation=conversation
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages in a conversation"""
        conversation = self.get_object()

        # Check if user is participant in conversation
        if request.user not in conversation.participants.all():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        """Filter messages to show only those in user's conversations"""
        user = self.request.user
        if user.is_authenticated:
            user_conversations = Conversation.objects.filter(participants=user)
            return Message.objects.filter(conversation__in=user_conversations)
        return Message.objects.none()

    def perform_create(self, serializer):
        """Set the sender to the current user when creating a message"""
        conversation_id = self.request.data.get('conversation')
        conversation = get_object_or_404(Conversation, pk=conversation_id)

        # Check if user is participant in conversation
        if self.request.user not in conversation.participants.all():
            raise serializers.ValidationError("You are not a participant in this conversation")

        serializer.save(sender=self.request.user)