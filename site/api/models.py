from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from . import broker_api_tasks
from config import settings


class ManagerSyncBroker(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        user = super()._create_user(username, email, password, **extra_fields)
        broker_api_tasks.create_user.delay(user_id=user.id, password=password)
        return user

class UserSyncBroker(AbstractUser):
    objects = ManagerSyncBroker()

    def delete(self, *args, **kwargs):
        broker_api_tasks.delete_user.delay(self.pk)
        super().delete(*args, **kwargs)


class Room(models.Model):
    objects = models.manager.Manager()

    name = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=32)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-id',)

    def save(self, *args, **kwargs):
        created = self.pk is None

        super().save(*args, **kwargs)

        if created:
            UserPermissionForRoom.objects.create(room=self, user=self.owner)

    def delete(self, *args, **kwargs):
        broker_api_tasks.delete_vhost.delay(self.pk)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class UserPermissionForRoom(models.Model):
    objects = models.manager.Manager()

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('room', 'user')
        ordering = ('-id',)

    def save(self, *args, **kwargs):
        if self.pk:
            old = self.__class__.objects.get(pk=self.pk)
            if old.room != self.room or old.user != self.user:
                broker_api_tasks.delete_permission.delay(old.room.id, old.user.id)

        super().save(*args, **kwargs)
        broker_api_tasks.create_vhost_and_set_permission.delay(self.room.pk, self.user.pk)

    def delete(self, *args, **kwargs):
        broker_api_tasks.delete_permission.delay(self.room.pk, self.user.pk)
        super().delete(*args, **kwargs)
