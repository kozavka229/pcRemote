from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Room, UserPermissionForRoom


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
    password = serializers.CharField(write_only=True, default='', label='Password')

    class Meta:
        model = Room
        fields = ('url', 'name', 'password')

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return Room.objects.create(
            name=validated_data['name'],
            password=make_password(validated_data['password']),
            owner=validated_data['owner']
        )

    def update(self, instance, validated_data):
        instance.name = validated_data['name']
        instance.password = make_password(validated_data['password'])
        instance.save()
        return instance


class UserPermissionForRoomSerializer(serializers.ModelSerializer):
    user = serializers.CharField()
    room = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = UserPermissionForRoom
        fields = ('user', 'room', 'password')

    def validate_user(self, value: str):
        try:
            user = get_user_model().objecs.get(username=value)
        except get_user_model().DoesNotExist:
            raise ValidationError('Пользователя не существует')
        return user

    def validate_room(self, value: str):
        try:
            room = Room.objects.get(name=value)
        except Room.DoesNotExist:
            raise ValidationError('Комнаты не существует')
        return room

    def validate(self, attrs):
        if not check_password(attrs['password'], attrs['room'].password):
            raise ValidationError('Неверный пароль комнаты')
        return attrs

    def create(self, validated_data):
        return UserPermissionForRoom.objects.create(room=validated_data['room'], user=validated_data['user'])


class SelfPermissionForRoomSerializer(UserPermissionForRoomSerializer):
    class Meta(UserPermissionForRoomSerializer.Meta):
        fields = ('room', 'password')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
