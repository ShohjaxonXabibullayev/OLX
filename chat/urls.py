from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, MessageListCreateView

router = DefaultRouter()
router.register(r"rooms", ChatRoomViewSet, basename="chatroom")

urlpatterns = [
    path("rooms/<int:room_id>/messages/", MessageListCreateView.as_view(), name="room_message_list"),
    path("", include(router.urls)),
]
