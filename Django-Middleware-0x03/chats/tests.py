import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User, Conversation, Message
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer

# Get the custom user model
User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the User model"""

    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+1234567890',
            'role': 'guest'
        }

    def test_create_user(self):
        """Test creating a user with valid data"""
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            phone_number=self.user_data['phone_number'],
            role=self.user_data['role'],
            password='testpass123'
        )

        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.role, 'guest')
        self.assertTrue(isinstance(user.user_id, uuid.UUID))
        self.assertTrue(user.check_password('testpass123'))

    def test_user_string_representation(self):
        """Test the string representation of User"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        expected_str = "Test User (test@example.com)"
        self.assertEqual(str(user), expected_str)

    def test_user_email_unique(self):
        """Test that user email must be unique"""
        User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='testpass123'
        )

        with self.assertRaises(Exception):
            User.objects.create_user(
                username='user2',
                email='test@example.com',  # Same email
                password='testpass123'
            )

    def test_user_role_choices(self):
        """Test user role validation"""
        user = User.objects.create_user(
            username='hostuser',
            email='host@example.com',
            role='host',
            password='testpass123'
        )
        self.assertEqual(user.role, 'host')

        user2 = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            role='admin',
            password='testpass123'
        )
        self.assertEqual(user2.role, 'admin')


class ConversationModelTest(TestCase):
    """Test cases for the Conversation model"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            first_name='User',
            last_name='One',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            first_name='User',
            last_name='Two',
            password='testpass123'
        )

    def test_create_conversation(self):
        """Test creating a conversation"""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        self.assertTrue(isinstance(conversation.conversation_id, uuid.UUID))
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())

    def test_conversation_string_representation(self):
        """Test the string representation of Conversation"""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        expected_str = "Conversation: User One (user1@example.com), User Two (user2@example.com)"
        self.assertEqual(str(conversation), expected_str)

    def test_conversation_ordering(self):
        """Test that conversations are ordered by creation date (newest first)"""
        conv1 = Conversation.objects.create()
        conv2 = Conversation.objects.create()

        conversations = Conversation.objects.all()
        self.assertEqual(conversations[0], conv2)  # Newest first
        self.assertEqual(conversations[1], conv1)


class MessageModelTest(TestCase):
    """Test cases for the Message model"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            first_name='Sender',
            last_name='User',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='receiver',
            email='receiver@example.com',
            password='testpass123'
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_create_message(self):
        """Test creating a message"""
        message = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Hello, this is a test message!"
        )

        self.assertTrue(isinstance(message.message_id, uuid.UUID))
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.message_body, "Hello, this is a test message!")
        self.assertTrue(message.sent_at)

    def test_message_string_representation(self):
        """Test the string representation of Message"""
        message = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Test message"
        )

        expected_str = f"Message from {self.user1} at {message.sent_at}"
        self.assertEqual(str(message), expected_str)

    def test_message_ordering(self):
        """Test that messages are ordered by sent date (newest first)"""
        message1 = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="First message"
        )
        message2 = Message.objects.create(
            sender=self.user2,
            conversation=self.conversation,
            message_body="Second message"
        )

        messages = Message.objects.all()
        self.assertEqual(messages[0], message2)  # Newest first
        self.assertEqual(messages[1], message1)


class UserSerializerTest(TestCase):
    """Test cases for UserSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            phone_number='+1234567890',
            role='guest',
            password='testpass123'
        )

    def test_user_serializer_contains_expected_fields(self):
        """Test that serializer contains expected fields"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data

        expected_fields = {'user_id', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'created_at'}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_user_serializer_content(self):
        """Test the content of serialized user data"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data

        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['role'], 'guest')


class ConversationSerializerTest(TestCase):
    """Test cases for ConversationSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_conversation_serializer_contains_expected_fields(self):
        """Test that serializer contains expected fields"""
        serializer = ConversationSerializer(instance=self.conversation)
        data = serializer.data

        expected_fields = {'conversation_id', 'participants', 'messages', 'created_at'}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_conversation_serializer_with_messages(self):
        """Test conversation serializer includes messages"""
        message = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Test message"
        )

        serializer = ConversationSerializer(instance=self.conversation)
        data = serializer.data

        self.assertEqual(len(data['messages']), 1)
        self.assertEqual(data['messages'][0]['message_body'], 'Test message')


class UserAPITest(APITestCase):
    """Test cases for User API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_users_list(self):
        """Test retrieving list of users"""
        url = reverse('user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_user(self):
        """Test creating a new user"""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'host'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.get(email='new@example.com').role, 'host')

    def test_get_user_detail(self):
        """Test retrieving a specific user"""
        url = reverse('user-detail', kwargs={'pk': self.user.user_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')


class ConversationAPITest(APITestCase):
    """Test cases for Conversation API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

        self.client.force_authenticate(user=self.user1)

    def test_get_conversations_list(self):
        """Test retrieving list of conversations for authenticated user"""
        url = reverse('conversation-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_conversation(self):
        """Test creating a new conversation"""
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )

        url = reverse('conversation-list')
        data = {
            'participant_ids': [str(self.user1.user_id), str(user3.user_id)]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 2)

    def test_send_message_to_conversation(self):
        """Test sending a message to a conversation"""
        url = reverse('conversation-send-message', kwargs={'pk': self.conversation.conversation_id})
        data = {
            'message_body': 'Hello, this is a test message!'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        message = Message.objects.first()
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.message_body, 'Hello, this is a test message!')

    def test_send_message_to_conversation_not_participant(self):
        """Test sending message fails if user is not a participant"""
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user3)

        url = reverse('conversation-send-message', kwargs={'pk': self.conversation.conversation_id})
        data = {
            'message_body': 'This should fail!'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_conversation_messages(self):
        """Test retrieving messages from a conversation"""
        # Create some messages
        Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Message 1"
        )
        Message.objects.create(
            sender=self.user2,
            conversation=self.conversation,
            message_body="Message 2"
        )

        url = reverse('conversation-messages', kwargs={'pk': self.conversation.conversation_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class MessageAPITest(APITestCase):
    """Test cases for Message API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

        self.message = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Test message"
        )

        self.client.force_authenticate(user=self.user1)

    def test_get_messages_list(self):
        """Test retrieving list of messages for authenticated user"""
        url = reverse('message-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_message(self):
        """Test creating a new message"""
        url = reverse('message-list')
        data = {
            'conversation': str(self.conversation.conversation_id),
            'message_body': 'New test message!'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 2)

        new_message = Message.objects.get(message_body='New test message!')
        self.assertEqual(new_message.sender, self.user1)

    def test_create_message_not_participant(self):
        """Test creating message fails if user is not conversation participant"""
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user3)

        url = reverse('message-list')
        data = {
            'conversation': str(self.conversation.conversation_id),
            'message_body': 'This should fail!'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_message_detail(self):
        """Test retrieving a specific message"""
        url = reverse('message-detail', kwargs={'pk': self.message.message_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message_body'], 'Test message')


class AuthenticationTest(APITestCase):
    """Test cases for API authentication"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        url = reverse('user-list')
        response = self.client.get(url)

        # Should require authentication
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access_allowed(self):
        """Test that authenticated requests are allowed"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PermissionTest(APITestCase):
    """Test cases for API permissions"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )

        # Create conversation between user1 and user2
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_user_can_only_see_own_conversations(self):
        """Test that users can only see conversations they participate in"""
        # Create another conversation without user3
        other_conversation = Conversation.objects.create()
        other_conversation.participants.add(self.user1, self.user2)

        # User3 should not see any conversations
        self.client.force_authenticate(user=self.user3)
        url = reverse('conversation-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # User1 should see the conversation
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both conversations

    def test_user_can_only_see_own_messages(self):
        """Test that users can only see messages from their conversations"""
        # Create message in conversation
        Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Private message"
        )

        # User3 should not see any messages
        self.client.force_authenticate(user=self.user3)
        url = reverse('message-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # User1 should see the message
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)