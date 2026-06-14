from django.contrib import admin
from .models import ChatRoom, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "text", "image", "is_read", "created_at")
    can_delete = False

class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "ad", "buyer", "seller", "created_at")
    list_filter = ("created_at",)
    search_fields = ("ad__title", "buyer__email", "seller__email")
    inlines = [MessageInline]

admin.site.register(ChatRoom, ChatRoomAdmin)
