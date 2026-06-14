from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.serializers import UserSerializer
from ads.serializers import AdSerializer
from .models import ChatRoom, Message

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source="sender.email", read_only=True)
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "room", "sender", "sender_email", "sender_name", "text", "image", "is_read", "created_at")
        read_only_fields = ("id", "room", "sender", "is_read", "created_at")

class ChatRoomSerializer(serializers.ModelSerializer):
    buyer_details = UserSerializer(source="buyer", read_only=True)
    seller_details = UserSerializer(source="seller", read_only=True)
    ad_details = AdSerializer(source="ad", read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ("id", "ad", "ad_details", "buyer", "buyer_details", "seller", "seller_details", "last_message", "unread_count", "created_at")
        read_only_fields = ("id", "buyer", "seller", "created_at")

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by("-created_at").first()
        if last_msg:
            return MessageSerializer(last_msg, context=self.context).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
