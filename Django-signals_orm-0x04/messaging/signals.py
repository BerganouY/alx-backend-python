from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Message, MessageHistory

@receiver(pre_save, sender=Message)
def track_message_edits(sender, instance, **kwargs):
    if instance.pk:  # Only for existing messages
        try:
            original = Message.objects.get(pk=instance.pk)
            if original.content != instance.content:  # Content changed
                MessageHistory.objects.create(
                    message=instance,
                    old_content=original.content,
                    edited_by=instance.sender
                )
                instance.is_edited = True
                instance.edited_at = timezone.now()
        except Message.DoesNotExist:
            pass  # New message being created