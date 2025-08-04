from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Message, Notification

User = get_user_model()


class SignalTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@test.com',
            password='testpass123'
        )

    def test_notification_created_on_message(self):
        # Create a new message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message content"
        )

        # Check if notification was created
        notification = Notification.objects.filter(
            user=self.receiver,
            message=message
        ).first()

        self.assertIsNotNone(notification)
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)