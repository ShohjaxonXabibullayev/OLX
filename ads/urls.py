from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryListView, LocationListView, AdViewSet

router = DefaultRouter()
router.register(r"ads", AdViewSet, basename="ad")

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("locations/", LocationListView.as_view(), name="location_list"),
    path("", include(router.urls)),
]
