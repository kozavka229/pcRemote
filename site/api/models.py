from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.signals import post_delete, post_save

from . import broker_api_tasks
from config import settings


class ManagerSyncBroker(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        user = super()._create_user(username, email, password, **extra_fields)
        broker_api_tasks.create_user.delay(user_id=user.id, password=password)
        return user

class UserSyncBroker(AbstractUser):
    objects = ManagerSyncBroker()

    @classmethod
    def post_delete(cls, sender, instance, *__, **___):
        broker_api_tasks.delete_user.delay(instance.id)


class Room(models.Model):
    name = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=32)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    @classmethod
    async def post_save(cls, sender, instance, created, *__, **___):
        if created:
            broker_api_tasks.create_vhost_and_set_permission.delay(instance.id, instance.owner.id)

    @classmethod
    def post_delete(cls, sender, instance, *__, **___):
        broker_api_tasks.delete_vhost.delay(instance.id)


post_save.connect(Room.post_save, sender=Room)
post_delete.connect(Room.post_delete, sender=Room)
post_delete.connect(UserSyncBroker.post_delete, sender=UserSyncBroker)
