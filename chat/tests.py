from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from ads.models import Ad, Category, Location
from .models import ChatRoom, Message

User = get_user_model()

class ChatTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="password123",
            full_name="Owner User",
            profile_type="INDIVIDUAL"
        )
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="password123",
            full_name="Buyer User",
            profile_type="INDIVIDUAL"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            full_name="Other User",
            profile_type="INDIVIDUAL"
        )

        self.category = Category.objects.create(name="Items", slug="items")
        self.location = Location.objects.create(region="Tashkent", district="Yunusabad")
        
        self.ad = Ad.objects.create(
            title="Sofa",
            description="Comfortable sofa",
            price=150.00,
            category=self.category,
            location=self.location,
            owner=self.owner,
            status="ACTIVE"
        )

        self.room_list_url = reverse("chatroom-list")

    def test_create_chat_room_success(self):
        self.client.force_authenticate(user=self.buyer)
        data = {"ad": self.ad.id}
        response = self.client.post(self.room_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["ad"], self.ad.id)
        self.assertEqual(response.data["buyer"], self.buyer.id)
        self.assertEqual(response.data["seller"], self.owner.id)

    def test_create_chat_room_with_self_fails(self):
        self.client.force_authenticate(user=self.owner)
        data = {"ad": self.ad.id}
        response = self.client.post(self.room_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_messaging_flow(self):
        # 1. Create room
        room = ChatRoom.objects.create(ad=self.ad, buyer=self.buyer, seller=self.owner)
        
        # 2. Buyer sends a message
        self.client.force_authenticate(user=self.buyer)
        msg_url = reverse("room_message_list", args=[room.id])
        
        data = {"text": "Hello, is this still available?"}
        response = self.client.post(msg_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], data["text"])
        self.assertFalse(response.data["is_read"])
        
        # 3. Seller lists messages (which should mark them as read)
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(msg_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # Check database directly to see if is_read updated to True
        msg_in_db = Message.objects.get(id=response.data[0]["id"])
        self.assertTrue(msg_in_db.is_read)

    def test_chat_room_unread_count_and_preview(self):
        room = ChatRoom.objects.create(ad=self.ad, buyer=self.buyer, seller=self.owner)
        
        # Buyer sends two messages
        Message.objects.create(room=room, sender=self.buyer, text="First msg")
        Message.objects.create(room=room, sender=self.buyer, text="Second msg")
        
        # Authenticate as seller
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.room_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["unread_count"], 2)
        self.assertEqual(response.data[0]["last_message"]["text"], "Second msg")

    def test_other_user_cannot_access_chat(self):
        room = ChatRoom.objects.create(ad=self.ad, buyer=self.buyer, seller=self.owner)
        
        self.client.force_authenticate(user=self.other_user)
        msg_url = reverse("room_message_list", args=[room.id])
        response = self.client.get(msg_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
