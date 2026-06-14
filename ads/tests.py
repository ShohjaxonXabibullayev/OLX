import tempfile
from PIL import Image
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Category, Location, Ad, AdImage

User = get_user_model()

def get_temp_image():
    img = Image.new("RGB", (100, 100), color="red")
    tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(tmp_file, format="JPEG")
    tmp_file.seek(0)
    return SimpleUploadedFile(
        name="test_image.jpg",
        content=tmp_file.read(),
        content_type="image/jpeg"
    )

class AdAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="password123",
            full_name="Ad Owner",
            profile_type="INDIVIDUAL"
        )
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="password123",
            full_name="Buyer User",
            profile_type="INDIVIDUAL"
        )
        
        self.parent_cat = Category.objects.create(name="Vehicles", slug="vehicles")
        self.child_cat = Category.objects.create(name="Cars", slug="cars", parent=self.parent_cat)
        self.location = Location.objects.create(region="Tashkent", district="Chilanzar")
        
        self.ad = Ad.objects.create(
            title="Chevrolet Cobalt 2023",
            description="Perfect condition Cobalt",
            price=12000.00,
            currency="USD",
            category=self.child_cat,
            location=self.location,
            owner=self.user,
            status="ACTIVE",
            attributes={"year": 2023, "color": "white", "mileage": 15000}
        )

        self.list_create_url = reverse("ad-list")
        self.detail_url = reverse("ad-detail", args=[self.ad.id])
        self.categories_url = reverse("category_list")

    def test_nested_categories(self):
        response = self.client.get(self.categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return list of root categories
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Vehicles")
        # Should contain nested children
        self.assertEqual(len(response.data[0]["children"]), 1)
        self.assertEqual(response.data[0]["children"][0]["name"], "Cars")

    def test_ad_retrieve_increments_views(self):
        initial_views = self.ad.views_count
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ad.refresh_from_db()
        self.assertEqual(self.ad.views_count, initial_views + 1)

    def test_ad_creation_with_images_and_webp_conversion(self):
        self.client.force_authenticate(user=self.user)
        image = get_temp_image()
        
        data = {
            "title": "Gentra 2024",
            "description": "Brand new Gentra",
            "price": 14000.00,
            "currency": "USD",
            "category": self.child_cat.id,
            "location": self.location.id,
            "attributes": '{"year": 2024, "color": "black"}',
            "uploaded_images": [image]
        }
        # Multi-part post request
        response = self.client.post(self.list_create_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify WebP conversion on database model
        new_ad_id = response.data["id"]
        ad_obj = Ad.objects.get(id=new_ad_id)
        self.assertEqual(ad_obj.images.count(), 1)
        
        ad_img = ad_obj.images.first()
        # Verify filename has changed to .webp
        self.assertTrue(ad_img.image.name.lower().endswith(".webp"))
        
        # Verify it can be opened and format is indeed WEBP
        img = Image.open(ad_img.image.path)
        self.assertEqual(img.format, "WEBP")

    def test_faceted_filtering(self):
        # Create another ad in parent category
        Ad.objects.create(
            title="Bicycle",
            description="Good bike",
            price=200.00,
            currency="USD",
            category=self.parent_cat,
            location=self.location,
            owner=self.user,
            status="ACTIVE",
            attributes={"type": "sport"}
        )

        # 1. Filter by recursive category (parent category should return child category ads too)
        response = self.client.get(self.list_create_url, {"category": self.parent_cat.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return both Cobalt (in Cars subcategory) and Bicycle (in Vehicles parent category)
        self.assertEqual(len(response.data), 2)

        # 2. Filter by child category only
        response = self.client.get(self.list_create_url, {"category": self.child_cat.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Chevrolet Cobalt 2023")

        # 3. Filter by dynamic attributes (year=2023)
        response = self.client.get(self.list_create_url, {"attr_year": 2023})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # 4. Filter by dynamic attributes (year=2024 - which doesn't match Cobalt)
        response = self.client.get(self.list_create_url, {"attr_year": 2024})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
