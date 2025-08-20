import json

from django.contrib.auth.hashers import check_password
from django.core.exceptions import BadRequest
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger
from rest_framework import permissions, viewsets, generics
from rest_framework.response import Response

from .models import Room
from .serializers import RoomSerializer, UserSerializer, UserRoomConnectSerializer
from . import broker_api_tasks


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer

class UserView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_object(self):
        return self.request.user

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Room.objects.filter(owner=self.request.user)

class ConnectUserToRoomView(generics.GenericAPIView):
    serializer_class = UserRoomConnectSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request, *_, **__):
        serializer = self.get_serializer(data=request.POST)
        serializer.is_valid(raise_exception=True)

        try:
            room = Room.objects.get(name=serializer.validated_data["room"])
        except Room.DoesNotExist:
            raise BadRequest("Комната не существует")

        if check_password(serializer.validated_data["password"], room.password):
            broker_api_tasks.set_permission.delay(room.id, request.user.id)
            return Response(status=204)

        raise BadRequest("Неправильный пароль")

# create room
# connect to room
# ---
# connect to broker via pika
# start message

@csrf_exempt
def endpoint(request, method: str):
    if request.method != "POST":
        return HttpResponse(status=400)

    params = json.loads(request.body)
    logger.info(params)
    getattr(broker_api_tasks, method).delay(**params)

    return HttpResponse()
