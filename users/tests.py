from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("auth_register")
        self.login_url = reverse("token_obtain_pair")
        self.me_url = reverse("auth_me")
        
        self.user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
            "phone_number": "+998901234567",
            "profile_type": "INDIVIDUAL",
        }

    def test_registration_success(self):
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.user_data["email"])
        self.assertEqual(response.data["user"]["profile_type"], "INDIVIDUAL")

    def test_registration_missing_profile_type(self):
        data = self.user_data.copy()
        data.pop("profile_type")
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_type", response.data)

    def test_registration_mismatched_passwords(self):
        data = self.user_data.copy()
        data["password_confirm"] = "differentpassword"
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_login_success(self):
        # Create user
        User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            full_name=self.user_data["full_name"],
            profile_type=self.user_data["profile_type"]
        )
        
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_profile_retrieval_and_update_restrictions(self):
        user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            full_name=self.user_data["full_name"],
            profile_type=self.user_data["profile_type"]
        )
        
        # Authenticate
        self.client.force_authenticate(user=user)
        
        # Get profile
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], user.full_name)
        
        # Try to update full_name and profile_type
        update_data = {
            "full_name": "Updated Name",
            "profile_type": "BUSINESS" # Should not be updated since profile_type is read_only after registration
        }
        response = self.client.patch(self.me_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], "Updated Name")
        self.assertEqual(response.data["profile_type"], "INDIVIDUAL") # Remains unchanged!
