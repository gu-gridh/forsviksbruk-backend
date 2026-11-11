"""
Forsviksbruk Viewer Tests
"""

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from digicure_viewer.models import Image, Panorama, PointCloud
from .models import Area, Article, ArticleArea, ArticleMedia, ArticleSpace


@pytest.mark.django_db
class TestArticleSpace:

    def test_only_one_media_object(self):
        article = Article.objects.create(title="Hammaren")
        space = ArticleSpace(article=article, order=1, video_url="https://example.org/video", image="a.jpg")
        with pytest.raises(ValidationError):
            space.full_clean()


@pytest.mark.django_db
class TestArticleMedia:
    """Exactly one resource per media row, linked to the article's area"""

    def setup_method(self):
        self.area = Area.objects.create(name="Smedja")
        self.article = Article.objects.create(title="Hammaren")
        ArticleArea.objects.create(article=self.article, area=self.area)

    def test_one_resource_is_valid(self):
        media = ArticleMedia(article=self.article, panorama=Panorama.objects.create(title="Yard"))
        media.full_clean()
        assert media.media_type == "panorama"

    def test_no_resource_is_invalid(self):
        with pytest.raises(ValidationError):
            ArticleMedia(article=self.article).full_clean()

    def test_two_resources_are_invalid(self):
        media = ArticleMedia(
            article=self.article,
            panorama=Panorama.objects.create(title="Yard"),
            pointcloud=PointCloud.objects.create(title="Forge scan"),
        )
        with pytest.raises(ValidationError):
            media.full_clean()

    def test_link_to_area(self):
        panorama = Panorama.objects.create(title="Yard")
        image = Image(title="Photo")
        image.save()
        for resource in ({"panorama": panorama}, {"image": image}):
            ArticleMedia.objects.create(article=self.article, **resource).link_to_area(self.area)
        assert list(panorama.place.all()) == [self.area]
        image.refresh_from_db()
        assert image.place == self.area


@pytest.mark.django_db
class TestArticleAPI:

    def setup_method(self):
        self.client = APIClient()
        area = Area.objects.create(name_sv="Smedja", name_en="Forge")
        self.article = Article.objects.create(title_sv="Hammaren", title_en="The hammer")
        ArticleArea.objects.create(article=self.article, area=area)
        ArticleSpace.objects.create(article=self.article, order=1, text_sv="Text")

    def test_translated_title(self):
        response = self.client.get(f"/sv/api/articles/{self.article.pk}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Hammaren"
        assert response.data["area_name"] == "Smedja"
        assert len(response.data["spaces"]) == 1
        assert response.data["media"] == []

    def test_falls_back_to_swedish(self):
        response = self.client.get(f"/de/api/articles/{self.article.pk}/")
        assert response.data["title"] == "Hammaren"
