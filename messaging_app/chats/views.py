from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from .models import User, Conversation, Message
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation, IsMessageSender, IsOwnerOrReadOnly
from .pagination import MessagePagination
from .filters import MessageFilter


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['role']  # Removed sensitive fields like email, phone

    def get_queryset(self):
        """Users can only see themselves and users they have conversations with"""
        if self.request.user.is_staff:
            return User.objects.all()

        # Non-staff users can only see:
        # 1. Themselves
        # 2. Users they share conversations with
        shared_conversation_users = User.objects.filter(
            conversations__participants=self.request.user
        ).distinct()

        return User.objects.filter(
            id__in=[self.request.user.id] + list(shared_conversation_users.values_list('id', flat=True))
        )

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'list']:
            # Only staff can create users or list all users
            permission_classes = [IsAuthenticated, IsStaff]
        else:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    serializer_class = ConversationSerializer
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        """Only show conversations where user is a participant"""
        return Conversation.objects.filter(participants=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsParticipantOfConversation])
    def send_message(self, request, *args, **kwargs):
        """Send message with proper validation"""
        conversation = self.get_object()

        # Validate conversation_id if provided in request data
        if 'conversation_id' in request.data:
            if str(request.data['conversation_id']) != str(conversation.id):
                return Response(
                    {'error': 'Conversation ID mismatch'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Ensure user is participant of the conversation
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'Access denied. You are not a participant of this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MessageSerializer(data=request.data, context={
            'request': request,
            'conversation': conversation
        })

        if serializer.is_valid():
            serializer.save(sender=request.user, conversation=conversation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsParticipantOfConversation])
    def messages(self, request, *args, **kwargs):
        """Get messages with proper access control"""
        conversation = self.get_object()

        # Double-check user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'Access denied. You are not a participant of this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = MessageFilter(
            request.GET,
            queryset=conversation.messages.all()
        ).qs.order_by('-created_at')  # Add ordering for consistency

        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsParticipantOfConversation])
    def add_participant(self, request, *args, **kwargs):
        """Add participant with proper authorization"""
        conversation = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_to_add = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if conversation.participants.filter(id=user_id).exists():
            return Response(
                {'error': 'User is already a participant'},
                status=status.HTTP_400_BAD_REQUEST
            )

        conversation.participants.add(user_to_add)
        return Response({'message': 'Participant added successfully'})


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
        ).select_related('sender', 'conversation').order_by('-created_at')

    def perform_create(self, serializer):
        """Automatically set sender and validate conversation access"""
        conversation_id = self.request.data.get('conversation_id')

        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                if not conversation.participants.filter(id=self.request.user.id).exists():
                    raise PermissionError("You are not a participant of this conversation")
                serializer.save(sender=self.request.user, conversation=conversation)
            except Conversation.DoesNotExist:
                raise ValidationError("Conversation not found")
        else:
            serializer.save(sender=self.request.user)

    def get_permissions(self):
        """Override permissions for different actions"""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsParticipantOfConversation]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsParticipantOfConversation, IsMessageSender]
        else:
            permission_classes = [IsAuthenticated, IsParticipantOfConversation]

        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsMessageSender])
    def mark_as_read(self, request, *args, **kwargs):
        """Mark message as read"""
        message = self.get_object()
        # Add your read status logic here
        return Response({'message': 'Message marked as read'})


# Additional custom permissions you'll need:
from rest_framework.permissions import BasePermission


class IsStaff(BasePermission):
    """Only allow staff users"""

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsOwnerOrReadOnly(BasePermission):
    """Allow owners to edit, others to read only"""

    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # Write permissions only for owner
        return obj == request.user