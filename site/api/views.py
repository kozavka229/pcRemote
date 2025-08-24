import loguru
from rest_framework import permissions, viewsets, generics
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Room, UserPermissionForRoom
from .serializers import RoomSerializer, UserSerializer, SelfPermissionForRoomSerializer


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
    serializer_class = SelfPermissionForRoomSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, *_, **__):
        return Response([{'id': perm.room.id, 'name': perm.room.name} for perm in self.get_queryset()])

    def post(self, request: Request, *_, **__):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=204)

    def get_queryset(self):
        return UserPermissionForRoom.objects.filter(user=self.request.user)
