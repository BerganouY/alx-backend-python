from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import generics

User = get_user_model()

class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(
            {"detail": "User account and all related data deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


    @api_view(['DELETE'])
    @permission_classes([IsAuthenticated])
    def delete_user(request):
        """
        Delete the authenticated user's account and all related data
        """
        user = request.user
        user.delete()
        return Response(
            {"detail": "User account and all related data deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
    )


class ThreadedMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # Optimized query with prefetch_related and select_related
        return Message.objects.filter(
            conversation=conversation
        ).select_related(
            'sender',
            'parent_message',
            'conversation'
        ).prefetch_related(
            'replies'
        ).order_by('timestamp')