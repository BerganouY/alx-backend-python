from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from .models import User, Conversation, Message
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation, IsMessageSender
from .pagination import MessagePagination
from .filters import MessageFilter


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['role', 'email', 'phone_number']


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        """Only show conversations where user is a participant"""
        return super().get_queryset().filter(participants=self.request.user)

    @action(detail=True, methods=['post'])
    def send_message(self, request, *args, **kwargs):
        """Send message handled by perform_create in MessageViewSet"""
        conversation = self.get_object()
        serializer = MessageSerializer(data=request.data, context={
            'request': request,
            'conversation': conversation
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def messages(self, request, *args, **kwargs):
        """Get messages through filtered queryset"""
        conversation = self.get_object()
        messages = MessageFilter(
            request.GET,
            queryset=conversation.messages.all()
        ).qs
        page = self.paginate_queryset(messages)
        serializer = MessageSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsParticipantOfConversation, IsMessageSender]
    pagination_class = MessagePagination
    serializer_class = MessageSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = MessageFilter

    def get_queryset(self):
        """Only show messages from conversations where user is a participant"""
        return Message.objects.filter(
            conversation__participants=self.request.user
        )

    def perform_create(self, serializer):
        """Automatically set sender from request user"""
        serializer.save(sender=self.request.user)