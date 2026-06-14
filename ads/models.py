import io
from PIL import Image
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile

def convert_to_webp(image_field):
    img = Image.open(image_field)
    output = io.BytesIO()
    
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    img.save(output, format="WEBP", quality=80)
    output.seek(0)
    
    original_name = image_field.name
    name_without_extension = original_name.rsplit(".", 1)[0]
    new_name = f"{name_without_extension}.webp"
    
    return ContentFile(output.read(), name=new_name)

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children"
    )
    icon = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return " -> ".join(full_path[::-1])

class Location(models.Model):
    region = models.CharField(max_length=100)
    district = models.CharField(max_length=100)

    class Meta:
        unique_together = ("region", "district")

    def __str__(self):
        return f"{self.region}, {self.district}"

class Ad(models.Model):
    CURRENCY_CHOICES = (
        ("UZS", "So'm"),
        ("USD", "Dollar"),
    )
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("MODERATION", "Moderation"),
        ("REJECTED", "Rejected"),
        ("ARCHIVED", "Archived"),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="UZS")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="ads")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ads")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name="ads")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="ACTIVE")
    attributes = models.JSONField(default=dict, blank=True)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class AdImage(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="ads/")
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image and not self.image.name.lower().endswith(".webp"):
            self.image = convert_to_webp(self.image)
        super().save(*args, **kwargs)
