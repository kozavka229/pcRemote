from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import Room


class UserSerializer(serializers.ModelSerializer):
    plain_password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'plain_password')
        extra_kwargs = {
            "id": {"read_only": True},
        }

    def create(self, validated_data):
        return get_user_model().objects.create_user(
            username=validated_data["username"],
            password=validated_data["plain_password"]
        )

    def update(self, instance, validated_data):
        instance.username = validated_data["username"]
        instance.set_password(validated_data["plain_password"])
        instance.save()
        return instance


class RoomSerializer(serializers.HyperlinkedModelSerializer):
    plain_password = serializers.CharField(write_only=True)

    class Meta:
        model = Room
        fields = ('url', 'name', 'plain_password')

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return Room.objects.create(
            name=validated_data['name'],
            password=make_password(validated_data['plain_password']),
            owner=validated_data['owner']
        )

    def update(self, instance, validated_data):
        instance.name = validated_data['name']
        instance.password = make_password(validated_data['plain_password'])
        instance.save()
        return instance


class UserRoomConnectSerializer(serializers.Serializer):
    room = serializers.CharField()
    password = serializers.CharField(write_only=True)
