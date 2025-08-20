from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Room


@admin.register(Room, get_user_model())
class AppAdmin(admin.ModelAdmin):
    pass

