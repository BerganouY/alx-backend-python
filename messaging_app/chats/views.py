from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from .models import User, Conversation, Message
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation
from .pagination import MessagePagination
from .filters import MessageFilter


class MessageFilter(filters.FilterSet):
    class Meta:
        model = Message
        fields = {
            'sent_at': ['gte', 'lte', 'exact'],
            'sender__user_id': ['exact'],
            'conversation__conversation_id': ['exact'],
            'message_body': ['icontains']
        }


class ConversationFilter(filters.FilterSet):
    class Meta:
        model = Conversation
        fields = {
            'created_at': ['gte', 'lte', 'exact'],
            'participants__user_id': ['exact']
        }


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for all user operations
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['role', 'email', 'phone_number']


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]  # Combined permissions
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ConversationFilter

    def get_queryset(self):
        """Filter conversations to show only those the user participates in"""
        return self.filter_queryset(
            Conversation.objects.filter(participants=self.request.user)
        )

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to a specific conversation"""
        conversation = self.get_object()
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
        """Get all messages in a conversation with optional filtering"""
        conversation = self.get_object()
        messages = conversation.messages.all()
        filtered_messages = MessageFilter(request.GET, queryset=messages).qs
        serializer = MessageSerializer(filtered_messages, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]  # Combined permissions
    pagination_class = MessagePagination
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = MessageFilter

    def get_queryset(self):
        """Filter messages to show only those in user's conversations"""
        return self.filter_queryset(
            Message.objects.filter(conversation__participants=self.request.user)
        )

    def perform_create(self, serializer):
        """Set the sender to the current user when creating a message"""
        conversation_id = self.request.data.get('conversation')
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        serializer.save(sender=self.request.user)