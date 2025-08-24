from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Room, UserPermissionForRoom


@admin.register(Room, get_user_model(), UserPermissionForRoom)
class AppAdmin(admin.ModelAdmin):
    pass

