from django.urls import path, include
from django.contrib import admin
from chats.auth import CustomTokenObtainPairView, CustomTokenRefreshView, RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chats.urls')),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
]