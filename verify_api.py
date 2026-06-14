import os
import django
import json

# Bootstrap Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from ads.models import Category, Location, Ad
from chat.models import ChatRoom, Message

User = get_user_model()

def run_verification():
    print("\n=============================================")
    print("      OLX BACKEND API VERIFICATION SCRIPT    ")
    print("=============================================\n")
    
    client = APIClient()
    
    # 1. Clean Database
    print("Cleaning database...")
    User.objects.all().delete()
    Category.objects.all().delete()
    Location.objects.all().delete()
    Ad.objects.all().delete()
    ChatRoom.objects.all().delete()
    Message.objects.all().delete()
    
    # 2. Test User Registration
    print("\n1. Testing User Registration...")
    reg_data = {
        "email": "shohjaxon@example.com",
        "full_name": "Shohjaxon Xabibullayev",
        "password": "mypassword123",
        "password_confirm": "mypassword123",
        "phone_number": "+998901234567",
        "profile_type": "BUSINESS"
    }
    res = client.post("/api/v1/auth/register/", reg_data, format="json")
    assert res.status_code == 201, f"Registration failed: {res.data}"
    print("   -> Status: 201 Created")
    print(f"   -> User: {res.data['user']['full_name']} ({res.data['user']['profile_type']})")
    
    user_id = res.data["user"]["id"]
    token = res.data["tokens"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    
    # 3. Test Profile Retrieval
    print("\n2. Testing Authenticated Profile Retrieval...")
    res = client.get("/api/v1/auth/me/")
    assert res.status_code == 200
    assert res.data["email"] == "shohjaxon@example.com"
    print("   -> Status: 200 OK")
    print(f"   -> Profile Data: {res.data}")
    
    # 4. Create Category and Location
    print("\n3. Creating Categories & Geolocation...")
    vehicles = Category.objects.create(name="Transport", slug="transport")
    cars = Category.objects.create(name="Yengil Mashinalar", slug="cars", parent=vehicles)
    loc = Location.objects.create(region="Tashkent", district="Mirzo Ulugbek")
    print(f"   -> Created Category: {cars}")
    print(f"   -> Created Location: {loc}")
    
    # 5. Create Ad
    print("\n4. Creating Classified Ad...")
    ad_data = {
        "title": "Chevrolet Cobalt 2024",
        "description": "Yangi Cobalt, oq rangda, 0 probeg.",
        "price": 13500.00,
        "currency": "USD",
        "category": cars.id,
        "location": loc.id,
        "attributes": {"year": 2024, "color": "white", "transmission": "automatic"}
    }
    res = client.post("/api/v1/ads/", ad_data, format="json")
    assert res.status_code == 201, f"Ad creation failed: {res.data}"
    ad_id = res.data["id"]
    
    # Force set status to MODERATION in DB for testing moderation flow since status is a read-only field in serializer
    ad_obj = Ad.objects.get(id=ad_id)
    ad_obj.status = "MODERATION"
    ad_obj.save()
    
    print("   -> Status: 201 Created")
    print(f"   -> Ad Title: {res.data['title']}")
    print(f"   -> Dynamic Specs: {res.data['attributes']}")
    
    # 6. Test Filtering
    print("\n5. Testing Ad Filtering & Moderation Status...")
    client.credentials() # Logout
    
    # Filter for year=2024. Ad is in MODERATION status, so it should not appear publicly.
    res = client.get("/api/v1/ads/", {"attr_year": 2024})
    assert res.status_code == 200
    assert len(res.data) == 0
    print("   -> Filtered (MODERATION status): 0 ads visible (SUCCESS)")
    
    # Approve the Ad
    ad_obj = Ad.objects.get(id=ad_id)
    ad_obj.status = "ACTIVE"
    ad_obj.save()
    print("   -> [Admin Action] Approved Ad (Status set to ACTIVE)")
    
    # Filter again. It should appear now.
    res = client.get("/api/v1/ads/", {"attr_year": 2024})
    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["title"] == "Chevrolet Cobalt 2024"
    print("   -> Filtered (ACTIVE status): 1 ad visible (SUCCESS)")
    
    # 7. Test Chat Room & Message Creation
    print("\n6. Testing P2P Messaging Flow...")
    buyer_user = User.objects.create_user(
        email="buyer@example.com",
        password="buyerpassword123",
        full_name="Abdurahmon",
        profile_type="INDIVIDUAL"
    )
    client.force_authenticate(user=buyer_user)
    
    # Create Chat Room
    res = client.post("/api/v1/chat/rooms/", {"ad": ad_id}, format="json")
    assert res.status_code == 201
    room_id = res.data["id"]
    print(f"   -> Created Chat Room ID: {room_id} (Buyer: Abdurahmon, Seller: Shohjaxon)")
    
    # Send message
    msg_data = {"text": "Assalomu alaykum, mashina hali sotilmadimi?"}
    res = client.post(f"/api/v1/chat/rooms/{room_id}/messages/", msg_data, format="json")
    assert res.status_code == 201
    print("   -> Message sent successfully")
    print(f"   -> Message content: '{res.data['text']}'")
    
    # 8. Check unread count as Seller
    print("\n7. Verifying Unread Message Count for Seller...")
    client.force_authenticate(user=User.objects.get(id=user_id)) # Authenticate as Seller (Shohjaxon)
    res = client.get("/api/v1/chat/rooms/")
    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["unread_count"] == 1
    assert res.data[0]["last_message"]["text"] == "Assalomu alaykum, mashina hali sotilmadimi?"
    print(f"   -> Unread count: {res.data[0]['unread_count']}")
    print(f"   -> Last message preview: '{res.data[0]['last_message']['text']}'")
    
    # Read the message
    msg_url = f"/api/v1/chat/rooms/{room_id}/messages/"
    res = client.get(msg_url)
    assert res.status_code == 200
    # Verify unread count is now 0
    res = client.get("/api/v1/chat/rooms/")
    assert res.data[0]["unread_count"] == 0
    print(f"   -> Read message: unread count updated to {res.data[0]['unread_count']}")
    
    print("\n=============================================")
    print("     ALL API VERIFICATIONS PASSED SUCCESSFULLY!    ")
    print("=============================================\n")

if __name__ == "__main__":
    run_verification()
