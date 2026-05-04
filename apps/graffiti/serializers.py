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
