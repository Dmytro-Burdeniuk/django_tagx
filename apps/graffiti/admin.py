from django.contrib import admin

from .models import Graffiti, Photo, Vote


@admin.register(Graffiti)
class GraffitiAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['title', 'description']


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['graffiti', 'uploaded_at']
    list_filter = ['uploaded_at']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['graffiti', 'user', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
