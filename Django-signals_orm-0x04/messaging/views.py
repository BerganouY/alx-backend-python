from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated

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