"""
Forsviksbruk Viewer Tests
"""

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from .models import Area, Article, ArticleSpace


@pytest.mark.django_db
class TestArticleSpace:

    def test_only_one_media_object(self):
        article = Article.objects.create(title="Hammaren")
        space = ArticleSpace(article=article, order=1, video_url="https://example.org/video", image="a.jpg")
        with pytest.raises(ValidationError):
            space.full_clean()


@pytest.mark.django_db
class TestArticleAPI:

    def setup_method(self):
        self.client = APIClient()
        area = Area.objects.create(name_sv="Smedja", name_en="Forge")
        self.article = Article.objects.create(area=area, title_sv="Hammaren", title_en="The hammer")
        ArticleSpace.objects.create(article=self.article, order=1, text_sv="Text")

    def test_translated_title(self):
        response = self.client.get(f"/sv/api/articles/{self.article.pk}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Hammaren"
        assert response.data["area_name"] == "Smedja"
        assert len(response.data["spaces"]) == 1

    def test_falls_back_to_swedish(self):
        response = self.client.get(f"/de/api/articles/{self.article.pk}/")
        assert response.data["title"] == "Hammaren"
