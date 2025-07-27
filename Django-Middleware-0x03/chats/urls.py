from django.urls import path, include
from rest_framework import routers  # Import routers module
from rest_framework_nested import routers as nested_routers
from .views import UserViewSet, ConversationViewSet, MessageViewSet

# Initialize main router (DefaultRouter)
main_router = routers.DefaultRouter()  # Now using routers.DefaultRouter() explicitly
main_router.register(r'users', UserViewSet, basename='users')
main_router.register(r'conversations', ConversationViewSet, basename='conversations')

# Create nested router for messages under conversations
conversations_router = nested_routers.NestedDefaultRouter(
    main_router,
    r'conversations',
    lookup='conversation'  # this will be available as kwargs['conversation'] in views
)
conversations_router.register(r'messages', MessageViewSet, basename='conversation-messages')

urlpatterns = [
    # Include both main and nested routers
    path('', include(main_router.urls)),
    path('', include(conversations_router.urls)),
]


"routers.DefaultRouter()"