"""
Example App Tests

Demonstrates testing patterns using the abstract test framework.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Place, Tag


@pytest.mark.django_db
class TestPlaceModel:
    """Tests for the Place model"""

    def test_create_place(self):
        place = Place.objects.create(name="Test Place", description="A test")
        assert place.name == "Test Place"
        assert place.published is True
        assert place.created_at is not None

    def test_str_representation(self):
        place = Place.objects.create(name="My Place")
        assert str(place) == "My Place"


@pytest.mark.django_db
class TestTagModel:
    """Tests for the Tag model"""

    def test_create_tag(self):
        tag = Tag.objects.create(text="history")
        assert tag.text == "history"

    def test_unique_text(self):
        Tag.objects.create(text="unique")
        with pytest.raises(Exception):
            Tag.objects.create(text="unique")


@pytest.mark.django_db
class TestPlaceAPI:
    """Tests for the Place API endpoints"""

    def setup_method(self):
        self.client = APIClient()
        self.place = Place.objects.create(
            name="API Place",
            description="Test via API",
        )

    def test_list_places(self):
        response = self.client.get("/api/example/places/")
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_place(self):
        response = self.client.get(f"/api/example/places/{self.place.pk}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "API Place"
