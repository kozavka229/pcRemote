from django.urls import path, include
from rest_framework import routers

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from . import views

@api_view(["GET"])
def api_root_view(request, *_, **kwargs):
    link = lambda x: reverse(x, request=request, format=kwargs.get("format"))
    return Response({
        'new user': link("user-new"),
        'current user': link("user-current"),
        "room's connects manage": link("user-connect"),
        'rooms manage': link("room-list"),
    })

class Router(routers.DefaultRouter):
    def get_api_root_view(self, *_, **__):
        return api_root_view


router = Router()
router.register(r"rooms", views.RoomViewSet, basename="room")

urlpatterns = [
    path('', include(router.urls)),
    path('user/new/', views.CreateUserView.as_view(), name="user-new"),
    path('user/', views.UserView.as_view(), name="user-current"),
    path('connect/', views.ConnectUserToRoomView.as_view(), name="user-connect"),
]
