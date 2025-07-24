from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import generics
from .serializers import UserSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    pass

class CustomTokenRefreshView(TokenRefreshView):
    pass

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer