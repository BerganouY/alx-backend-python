from django.urls import path, include
from rest_framework import routers
from .views import UserViewSet, ConversationViewSet, MessageViewSet

# Initialize the DefaultRouter using full module path
router = routers.DefaultRouter()

# Register viewsets with the router
router.register(r'users', UserViewSet, basename='user')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    # Include all router-generated URLs
    path('', include(router.urls)),
]