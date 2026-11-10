"""
Forsviksbruk Viewer Tests
"""

import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from digicure_viewer.models import Panorama, PointCloud
from .models import Area, Article, ArticleSpace, PlanAnnotation


@pytest.mark.django_db
class TestPlanAnnotation:
    """Resource fields must match the type of annotation"""

    def setup_method(self):
        self.pointcloud = PointCloud.objects.create(title="Forge scan")

    def test_matching_resource_is_valid(self):
        annotation = PlanAnnotation(
            position=Point(14.43, 58.97),
            annotation_type=PlanAnnotation.Type.POINTCLOUD,
            pointcloud=self.pointcloud,
            camera_position=[1.0, 2.0, 3.0],
            look_at=[0.0, 0.0, 0.0],
        )
        annotation.full_clean()
        assert annotation.resource == self.pointcloud

    def test_missing_resource_is_invalid(self):
        annotation = PlanAnnotation(position=Point(0, 0), annotation_type=PlanAnnotation.Type.PANORAMA)
        with pytest.raises(ValidationError) as error:
            annotation.full_clean()
        assert "panorama" in error.value.message_dict

    def test_other_resource_is_invalid(self):
        annotation = PlanAnnotation(
            position=Point(0, 0),
            annotation_type=PlanAnnotation.Type.PANORAMA,
            panorama=Panorama.objects.create(title="Yard"),
            pointcloud=self.pointcloud,
        )
        with pytest.raises(ValidationError) as error:
            annotation.full_clean()
        assert "pointcloud" in error.value.message_dict


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
