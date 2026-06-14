from django.contrib import admin
from .models import User

class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "phone_number", "profile_type", "is_staff", "is_active")
    list_filter = ("profile_type", "is_staff", "is_active")
    search_fields = ("email", "full_name", "phone_number")
    ordering = ("email",)

admin.site.register(User, UserAdmin)
