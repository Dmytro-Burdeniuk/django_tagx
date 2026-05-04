from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.db.models import Index

User = get_user_model()


class Graffiti(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='graffiti')
    location = models.PointField()  # PostGIS PointField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['author']),
            Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author.username}"


class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    graffiti = models.ForeignKey(
        Graffiti, on_delete=models.CASCADE, related_name='photos'
    )
    image = models.ImageField(upload_to='graffiti_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Photo for {self.graffiti.title}"


class Vote(models.Model):
    VOTE_CHOICES = [
        ('exists', 'Існує'),
        ('not_exists', 'Не існує'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4)
    graffiti = models.ForeignKey(
        Graffiti, on_delete=models.CASCADE, related_name='votes'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('graffiti', 'user')
        indexes = [
            Index(fields=['graffiti']),
            Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} voted {self.vote_type} on {self.graffiti.id}"
