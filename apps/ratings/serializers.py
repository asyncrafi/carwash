from rest_framework import serializers
from .models import Rating, Tip


class RatingSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(
        source='reviewer.full_name', read_only=True
    )
    reviewer_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = [
            'id', 'booking', 'stars', 'comment',
            'reviewer_name', 'reviewer_avatar', 'created_at',
        ]
        read_only_fields = ['id', 'reviewer_name', 'reviewer_avatar', 'created_at']

    def get_reviewer_avatar(self, obj):
        if obj.reviewer.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.reviewer.avatar.url)
            return obj.reviewer.avatar.url
        return None


class TipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tip
        fields = ['id', 'booking', 'amount', 'created_at']
        read_only_fields = ['id', 'created_at']
