import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _  # For translations (optional)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('host', 'Host'),
        ('admin', 'Admin'),
    ]

    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guest')
    created_at = models.DateTimeField(auto_now_add=True)

    # Explicitly define password (optional, since AbstractUser already includes it)
    password = models.CharField(_('password'), max_length=128)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"




# import uuid
# from django.contrib.auth.models import AbstractUser
# from django.db import models
#
#
# class User(AbstractUser):
#     ROLE_CHOICES = [
#         ('guest', 'Guest'),
#         ('host', 'Host'),
#         ('admin', 'Admin'),
#     ]
#
#     user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     first_name = models.CharField(max_length=150)
#     last_name = models.CharField(max_length=150)
#     email = models.EmailField(unique=True)
#     phone_number = models.CharField(max_length=20, null=True, blank=True)
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guest')
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
#
#     def __str__(self):
#         return f"{self.first_name} {self.last_name} ({self.email})"
#
#
# class Conversation(models.Model):
#     conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     participants = models.ManyToManyField(User, related_name='conversations')
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         ordering = ['-created_at']
#
#     def __str__(self):
#         participant_names = [str(user) for user in self.participants.all()[:2]]
#         return f"Conversation: {', '.join(participant_names)}"
#
#
# class Message(models.Model):
#     message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
#     conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
#     message_body = models.TextField()
#     sent_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         ordering = ['-sent_at']
#
#     def __str__(self):
#         return f"Message from {self.sender} at {self.sent_at}"