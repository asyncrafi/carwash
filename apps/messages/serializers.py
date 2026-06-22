from rest_framework import serializers
from .models import ChatMessage, CallLog


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True)
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_avatar = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'sender', 'sender_name', 'sender_avatar',
            'recipient', 'booking', 'text', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at']

    def get_sender_avatar(self, obj):
        request = self.context.get('request')
        if obj.sender.avatar and request:
            return request.build_absolute_uri(obj.sender.avatar.url)
        return None


class CallLogSerializer(serializers.ModelSerializer):
    caller = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CallLog
        fields = [
            'id', 'caller', 'callee', 'booking',
            'started_at', 'ended_at', 'duration_seconds', 'created_at'
        ]
        read_only_fields = ['id', 'caller', 'created_at']