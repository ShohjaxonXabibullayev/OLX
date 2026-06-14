from django.db import models
from django.conf import settings
from ads.models import Ad

class ChatRoom(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="chat_rooms")
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buyer_rooms"
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_rooms"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("ad", "buyer")

    def __str__(self):
        return f"Chat for Ad: {self.ad.title} (Buyer: {self.buyer.email})"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    image = models.ImageField(upload_to="chat/", null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender.email} at {self.created_at}"
