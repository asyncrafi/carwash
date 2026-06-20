from rest_framework import serializers
from .models import ChatMessage, CallLog


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'recipient', 'booking', 'text', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']


class CallLogSerializer(serializers.ModelSerializer):
    caller = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CallLog
        fields = ['id', 'caller', 'callee', 'booking', 'started_at', 'ended_at', 'duration_seconds', 'created_at']
        read_only_fields = ['id', 'caller', 'created_at']
