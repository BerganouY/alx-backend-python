from django.db import models

class UnreadMessagesManager(models.Manager):
    def for_user(self, user):
        return self.filter(
            receiver=user,
            is_read=False
        ).only('id', 'content', 'sender__username', 'timestamp')