from rest_framework import serializers
from .models import Rating, Tip


class RatingSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(
        source='reviewer.full_name', read_only=True
    )

    class Meta:
        model = Rating
        fields = [
            'id', 'booking', 'stars', 'comment',
            'reviewer_name', 'created_at',
        ]
        read_only_fields = ['id', 'reviewer_name', 'created_at']


class TipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tip
        fields = ['id', 'booking', 'amount', 'created_at']
        read_only_fields = ['id', 'created_at']
