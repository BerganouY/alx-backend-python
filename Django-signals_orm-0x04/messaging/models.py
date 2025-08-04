from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.id}"


class UnreadMessagesManager(models.Manager):
    def for_user(self, user):
        return self.filter(
            receiver=user,
            is_read=False
        ).only('id', 'content', 'sender', 'timestamp')


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    unread = UnreadMessagesManager()

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message {self.id} from {self.sender} to {self.receiver}"

    def mark_as_read(self):
        self.is_read = True
        self.save()


class MessageHistory(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='history'
    )
    old_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        ordering = ['-edited_at']
        verbose_name_plural = 'Message Histories'

    def __str__(self):
        return f"Edit of message {self.message.id} at {self.edited_at}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user} about message {self.message.id}"