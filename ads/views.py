from django.db import models
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from .models import Category, Location, Ad, AdImage
from .serializers import CategorySerializer, LocationSerializer, AdSerializer
from .permissions import IsOwnerOrReadOnly

class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        # Only return top-level categories. Subcategories are nested.
        return Category.objects.filter(parent=None)

class LocationListView(generics.ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (permissions.AllowAny,)

class AdViewSet(viewsets.ModelViewSet):
    serializer_class = AdSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)

    def get_queryset(self):
        queryset = Ad.objects.all()
        
        # Determine base status filtering
        my_ads = self.request.query_params.get("my_ads", "false").lower() == "true"
        if my_ads and self.request.user.is_authenticated:
            queryset = queryset.filter(owner=self.request.user)
        else:
            # Public view shows only ACTIVE ads
            queryset = queryset.filter(status="ACTIVE")

        # Filters
        category_id = self.request.query_params.get("category")
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                def get_descendants(cat):
                    cats = [cat.id]
                    for child in cat.children.all():
                        cats.extend(get_descendants(child))
                    return cats
                category_ids = get_descendants(category)
                queryset = queryset.filter(category_id__in=category_ids)
            except Category.DoesNotExist:
                pass

        region = self.request.query_params.get("region")
        if region:
            queryset = queryset.filter(location__region__iexact=region)

        district = self.request.query_params.get("district")
        if district:
            queryset = queryset.filter(location__district__iexact=district)

        min_price = self.request.query_params.get("min_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.query_params.get("max_price")
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        currency = self.request.query_params.get("currency")
        if currency:
            queryset = queryset.filter(currency__iexact=currency)

        q = self.request.query_params.get("q")
        if q:
            queryset = queryset.filter(
                models.Q(title__icontains=q) | models.Q(description__icontains=q)
            )

        # Dynamic JSON attributes filtering (e.g. ?attr_year=2024 -> attributes__year=2024)
        for param, value in self.request.query_params.items():
            if param.startswith("attr_"):
                attr_name = param[5:]
                parsed_value = value
                if value.isdigit():
                    parsed_value = int(value)
                elif value.lower() == "true":
                    parsed_value = True
                elif value.lower() == "false":
                    parsed_value = False
                else:
                    try:
                        parsed_value = float(value)
                    except ValueError:
                        pass
                queryset = queryset.filter(**{f"attributes__{attr_name}": parsed_value})

        # Sorting
        ordering = self.request.query_params.get("ordering", "-created_at")
        if ordering in ["price", "-price", "created_at", "-created_at", "views_count", "-views_count"]:
            queryset = queryset.order_by(ordering)
            
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=["views_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
