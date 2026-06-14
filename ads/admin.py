from django.contrib import admin
from .models import Category, Location, Ad, AdImage

class AdImageInline(admin.TabularInline):
    model = AdImage
    extra = 1

class AdAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "currency", "category", "owner", "location", "status", "views_count", "created_at")
    list_filter = ("status", "currency", "category", "created_at")
    search_fields = ("title", "description", "owner__email", "owner__full_name")
    inlines = [AdImageInline]
    readonly_fields = ("views_count",)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")

class LocationAdmin(admin.ModelAdmin):
    list_display = ("region", "district")
    list_filter = ("region",)
    search_fields = ("region", "district")

admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Ad, AdAdmin)
