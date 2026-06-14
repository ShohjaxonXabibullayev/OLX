from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.serializers import UserSerializer
from .models import Category, Location, Ad, AdImage

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "parent", "icon", "children")

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "region", "district")

class AdImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdImage
        fields = ("id", "image", "is_main", "created_at")

class AdSerializer(serializers.ModelSerializer):
    images = AdImageSerializer(many=True, read_only=True)
    category_details = CategorySerializer(source="category", read_only=True)
    location_details = LocationSerializer(source="location", read_only=True)
    owner_details = UserSerializer(source="owner", read_only=True)
    
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    class Meta:
        model = Ad
        fields = (
            "id", "title", "description", "price", "currency", 
            "category", "category_details", "owner", "owner_details",
            "location", "location_details", "status", "attributes",
            "views_count", "images", "uploaded_images", "created_at", "updated_at"
        )
        read_only_fields = ("id", "owner", "status", "views_count", "created_at", "updated_at")

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["owner"] = request.user
            
        ad = Ad.objects.create(**validated_data)
        for i, img in enumerate(uploaded_images):
            AdImage.objects.create(ad=ad, image=img, is_main=(i == 0))
        return ad

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        instance = super().update(instance, validated_data)
        if uploaded_images:
            has_images = instance.images.exists()
            for i, img in enumerate(uploaded_images):
                AdImage.objects.create(ad=instance, image=img, is_main=(not has_images and i == 0))
        return instance
