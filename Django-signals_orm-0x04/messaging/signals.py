from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Message, MessageHistory

@receiver(pre_save, sender=Message)
def log_message_history(sender, instance, **kwargs):
    """
    Creates a MessageHistory record when a message is edited
    """
    if instance.pk:  # Only for existing messages (updates)
        try:
            original_message = Message.objects.get(pk=instance.pk)
            if original_message.content != instance.content:  # Only if content changed
                # Create history record before the message is updated
                MessageHistory.objects.create(
                    message=instance,
                    old_content=original_message.content,
                    edited_by=instance.sender
                )
                # Mark the message as edited
                instance.edited = True
                instance.last_edited = timezone.now()
        except Message.DoesNotExist:
            pass  # New message being created, skip history