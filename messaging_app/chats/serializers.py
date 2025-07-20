from rest_framework import serializers
from .models import User, Conversation, Message


class UserSerializer(serializers.ModelSerializer):
    # Example of SerializerMethodField (could compute a custom field)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['user_id', 'first_name', 'last_name', 'full_name', 'email', 'phone_number', 'role', 'created_at']
        read_only_fields = ['user_id', 'created_at', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    # Example of explicit CharField with validation
    message_body = serializers.CharField(
        max_length=1000,
        error_messages={
            "blank": "Message cannot be empty.",
            "max_length": "Message is too long (max 1000 chars)."
        }
    )

    class Meta:
        model = Message
        fields = ['message_id', 'sender', 'conversation', 'message_body', 'sent_at']
        read_only_fields = ['message_id', 'sender', 'sent_at']


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    messages = MessageSerializer(many=True, read_only=True)

    # Example of SerializerMethodField (could compute unread count)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['conversation_id', 'participants', 'participant_ids', 'messages', 'unread_count', 'created_at']
        read_only_fields = ['conversation_id', 'created_at', 'unread_count']

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.exclude(sender=request.user).filter(read=False).count()
        return 0

    def validate_participant_ids(self, value):
        # Example of ValidationError usage
        if len(value) < 1:
            raise serializers.ValidationError("At least one participant is required.")
        return value

    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(**validated_data)

        if participant_ids:
            participants = User.objects.filter(user_id__in=participant_ids)
            conversation.participants.set(participants)

        return conversation



# from rest_framework import serializers
# from .models import User, Conversation, Message
#
#
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['user_id', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'created_at']
#         read_only_fields = ['user_id', 'created_at']
#
#
# class MessageSerializer(serializers.ModelSerializer):
#     sender = UserSerializer(read_only=True)
#
#     class Meta:
#         model = Message
#         fields = ['message_id', 'sender', 'conversation', 'message_body', 'sent_at']
#         read_only_fields = ['message_id', 'sender', 'sent_at']
#
#
# class ConversationSerializer(serializers.ModelSerializer):
#     participants = UserSerializer(many=True, read_only=True)
#     participant_ids = serializers.ListField(
#         child=serializers.UUIDField(),
#         write_only=True,
#         required=False
#     )
#     messages = MessageSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Conversation
#         fields = ['conversation_id', 'participants', 'participant_ids', 'messages', 'created_at']
#         read_only_fields = ['conversation_id', 'created_at']
#
#     def create(self, validated_data):
#         participant_ids = validated_data.pop('participant_ids', [])
#         conversation = Conversation.objects.create()
#
#         if participant_ids:
#             participants = User.objects.filter(user_id__in=participant_ids)
#             conversation.participants.set(participants)
#
#         return conversation