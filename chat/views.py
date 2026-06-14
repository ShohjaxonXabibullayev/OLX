from django.db import models
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from ads.models import Ad
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer

class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(models.Q(buyer=user) | models.Q(seller=user)).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        ad_id = request.data.get("ad")
        if not ad_id:
            return Response({"ad": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        ad = get_object_or_404(Ad, id=ad_id)
        buyer = request.user

        if ad.owner == buyer:
            return Response({"detail": "You cannot start a chat for your own ad."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            room, created = ChatRoom.objects.get_or_create(ad=ad, buyer=buyer, seller=ad.owner)
            serializer = self.get_serializer(room)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(serializer.data, status=status_code)
        except IntegrityError:
            room = ChatRoom.objects.get(ad=ad, buyer=buyer)
            serializer = self.get_serializer(room)
            return Response(serializer.data, status=status_code)

class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_room(self):
        room_id = self.kwargs.get("room_id")
        room = get_object_or_404(ChatRoom, id=room_id)
        if room.buyer != self.request.user and room.seller != self.request.user:
            self.permission_denied(self.request, message="You do not have permission to access this chat room.")
        return room

    def get_queryset(self):
        room = self.get_room()
        queryset = Message.objects.filter(room=room)
        
        # Auto mark other user's messages as read on list retrieval
        queryset.filter(is_read=False).exclude(sender=self.request.user).update(is_read=True)
        return queryset

    def perform_create(self, serializer):
        room = self.get_room()
        serializer.save(sender=self.request.user, room=room)
