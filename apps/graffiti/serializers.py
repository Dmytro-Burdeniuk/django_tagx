from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Graffiti, Photo, Vote

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']
        read_only_fields = ['id', 'username']


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def validate_image(self, value):
        # Verify file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only JPEG, PNG, and WebP images are allowed")

        # Verify file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Image size must not exceed 5MB")

        return value


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'vote_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class VoteStatisticsSerializer(serializers.Serializer):
    exists = serializers.IntegerField(read_only=True)
    not_exists = serializers.IntegerField(read_only=True)


class GraffitiListSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(read_only=True)
    photos = PhotoSerializer(many=True, read_only=True)
    votes_statistics = serializers.SerializerMethodField()

    class Meta:
        model = Graffiti
        fields = ['id', 'title', 'description', 'author', 'location', 'photos', 'votes_statistics', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_votes_statistics(self, obj):
        exists_count = obj.votes.filter(vote_type='exists').count()
        not_exists_count = obj.votes.filter(vote_type='not_exists').count()
        return {
            'exists': exists_count,
            'not_exists': not_exists_count,
        }


class GraffitiDetailSerializer(GraffitiListSerializer):
    photos = PhotoSerializer(many=True, read_only=True)
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Graffiti
        fields = ['id', 'title', 'description', 'author', 'location', 'photos', 'votes_statistics', 'user_vote', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = obj.votes.filter(user=request.user).first()
            if vote:
                return {'id': str(vote.id), 'vote_type': vote.vote_type}
        return None


class GraffitiCreateUpdateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Graffiti
        fields = ['id', 'title', 'description', 'latitude', 'longitude', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        if len(value) > 255:
            raise serializers.ValidationError("Title must not exceed 255 characters")
        return value

    def validate_description(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long")
        return value

    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

    def create(self, validated_data):
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')

        from django.contrib.gis.geos import Point
        validated_data['location'] = Point(longitude, latitude)
        validated_data['author'] = self.context['request'].user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'latitude' in validated_data or 'longitude' in validated_data:
            from django.contrib.gis.geos import Point
            latitude = validated_data.pop('latitude', instance.location.y)
            longitude = validated_data.pop('longitude', instance.location.x)
            validated_data['location'] = Point(longitude, latitude)

        return super().update(instance, validated_data)
