"""
Forsviksbruk Viewer Tests
"""

import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from digicure_viewer.models import Author, Image, Panorama, PointCloud, Technique3D
from .models import (
    Area, Article, ArticleArea, ArticleLink, ArticleMedia, ArticleSpace, PointcloudAnnotation, validate_embed_code,
)


@pytest.mark.django_db
class TestArticleSpace:

    IFRAME = '<iframe src="https://www.youtube.com/embed/abc" allowfullscreen></iframe>'

    def test_image_sound_and_video_in_one_space(self):
        article = Article.objects.create(title="Hammaren")
        space = ArticleSpace(
            article=article, order=1, image="a.jpg", sound="b.mp3",
            sound_embed='<iframe src="https://w.soundcloud.com/player/?url=x"></iframe>',
            video_url=self.IFRAME,
        )
        space.full_clean()

    @pytest.mark.parametrize("value", [
        "https://example.org/video",
        IFRAME,
        '<audio controls><source src="https://example.org/a.mp3" type="audio/mpeg"></audio>',
    ])
    def test_embed_code_allowed(self, value):
        validate_embed_code(value)

    @pytest.mark.parametrize("value", [
        "<script>alert(1)</script>",
        '<iframe src="https://example.org" onload="alert(1)"></iframe>',
        '<iframe src="javascript:alert(1)"></iframe>',
        '<img src="x" onerror="alert(1)">',
        "javascript:alert(1)",
    ])
    def test_embed_code_rejected(self, value):
        with pytest.raises(ValidationError):
            validate_embed_code(value)


@pytest.mark.django_db
class TestArticleMedia:
    """One resource of the chosen type, linked to the article's area"""

    def setup_method(self):
        self.area = Area.objects.create(name="Smedja")
        self.article = Article.objects.create(title="Hammaren")
        ArticleArea.objects.create(article=self.article, area=self.area)

    def test_resource_of_chosen_type_is_valid(self):
        media = ArticleMedia(article=self.article, media_type="panorama", panorama=Panorama.objects.create(title="Yard"))
        media.full_clean()
        assert media.resource.title == "Yard"

    def test_missing_resource_is_invalid(self):
        with pytest.raises(ValidationError) as error:
            ArticleMedia(article=self.article, media_type="panorama").full_clean()
        assert "panorama" in error.value.message_dict

    def test_other_types_are_dropped(self):
        media = ArticleMedia(
            article=self.article,
            media_type="panorama",
            panorama=Panorama.objects.create(title="Yard"),
            pointcloud=PointCloud.objects.create(title="Forge scan"),
        )
        media.full_clean()
        assert media.pointcloud is None

    def test_link_to_area(self):
        panorama = Panorama.objects.create(title="Yard")
        image = Image(title="Photo")
        image.save()
        ArticleMedia(article=self.article, media_type="panorama", panorama=panorama).link_to_area(self.area)
        ArticleMedia(article=self.article, media_type="image", image=image).link_to_area(self.area)
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
        assert response.data["advanced_media"] is None

    def test_falls_back_to_swedish(self):
        response = self.client.get(f"/de/api/articles/{self.article.pk}/")
        assert response.data["title"] == "Hammaren"

    def test_location_is_lat_lng(self):
        self.article.location = Point(14.4371, 58.5844, srid=4326)
        self.article.save()
        response = self.client.get(f"/sv/api/articles/{self.article.pk}/")
        assert response.data["location"] == {"lat": 58.5844, "lng": 14.4371}

    def test_advanced_media_urls(self):
        panorama = Panorama.objects.create(title="Yard", url_public="https://example.org/panorama/yard/")
        ArticleMedia.objects.create(article=self.article, media_type="panorama", panorama=panorama)
        media = self.client.get(f"/sv/api/articles/{self.article.pk}/").data["advanced_media"]
        assert media["url"] == "https://example.org/panorama/yard/"
        assert media["iiif_url"] is None
        assert media["preview_url"] is None

    def test_advanced_media_preview_url(self, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        upload = SimpleUploadedFile("yard.png", b"\x89PNG", content_type="image/png")
        panorama = Panorama.objects.create(title="Yard", preview_image=upload)
        assert panorama.preview_image.name.startswith("digicure_viewer/original/")
        ArticleMedia.objects.create(article=self.article, media_type="panorama", panorama=panorama)
        media = self.client.get(f"/sv/api/articles/{self.article.pk}/").data["advanced_media"]
        assert media["preview_url"].endswith(panorama.preview_image.url)


@pytest.mark.django_db
class TestArticleInfoAPI:
    """/api/article_info/?id=<id>: all details of one article"""

    def setup_method(self):
        self.client = APIClient()
        self.area = Area.objects.create(name_sv="Smedja", description_sv="Smedjan vid ån")
        self.article = Article.objects.create(title_sv="Hammaren", location=Point(14.4371, 58.5844, srid=4326))
        ArticleArea.objects.create(article=self.article, area=self.area)
        ArticleSpace.objects.create(article=self.article, order=1, text_sv="Text", caption_sv="Bild")
        ArticleLink.objects.create(article=self.article, order=1, url="https://example.org", label_sv="Läs mer")
        self.other = Article.objects.create(title_sv="Dammen")

    def get(self, **params):
        response = self.client.get("/sv/api/article_info/", params)
        assert response.status_code == status.HTTP_200_OK
        return response.data["results"]

    def test_filter_by_id(self):
        results = self.get(id=self.article.pk)
        assert [r["id"] for r in results] == [self.article.pk]
        info = results[0]
        assert info["title"] == "Hammaren"
        assert info["area"] == {"id": self.area.pk, "name": "Smedja", "description": "Smedjan vid ån"}
        assert info["location"] == {"lat": 58.5844, "lng": 14.4371}
        assert info["spaces"][0]["text"] == "Text"
        assert info["links"][0]["label"] == "Läs mer"
        assert info["advanced_media"] is None
        assert info["pointcloud_annotations"] == []
        assert info["created_at"] and info["updated_at"]

    def test_unknown_id_is_empty(self):
        assert self.get(id=999999) == []

    def test_detail_route(self):
        response = self.client.get(f"/sv/api/article_info/{self.article.pk}/")
        assert response.data["id"] == self.article.pk

    def test_pointcloud_media_metadata(self):
        author = Author.objects.create(firstname="Ada", lastname="Lovelace")
        cloud = PointCloud.objects.create(
            title="Forge scan", description="Laser scan", url_public="https://example.org/pc/",
            url_download="https://example.org/pc.zip", technique=Technique3D.objects.create(text="Lidar"),
            camera_position=[1.0, 2.0, 3.0],
        )
        cloud.author.add(author)
        ArticleMedia.objects.create(article=self.article, media_type="pointcloud", pointcloud=cloud)
        annotation = PointcloudAnnotation.objects.create(pointcloud=cloud, article=self.other, position=[1.0, 1.0, 1.0])

        media = self.get(id=self.article.pk)[0]["advanced_media"]
        assert media["type"] == "pointcloud"
        assert media["title"] == "Forge scan"
        assert media["description"] == "Laser scan"
        assert media["url"] == "https://example.org/pc/"
        assert media["download_url"] == "https://example.org/pc.zip"
        assert media["technique"] == "Lidar"
        assert media["authors"] == [{"id": author.pk, "firstname": "Ada", "lastname": "Lovelace"}]
        assert media["camera_position"] == [1.0, 2.0, 3.0]
        assert media["annotations"] == [{"id": annotation.pk, "position": [1.0, 1.0, 1.0], "article": self.other.pk}]
        # The annotation opens the other article
        other = self.get(id=self.other.pk)[0]
        assert other["pointcloud_annotations"] == [{"id": annotation.pk, "pointcloud": cloud.pk, "position": [1.0, 1.0, 1.0]}]

    def test_panorama_media_metadata(self):
        panorama = Panorama.objects.create(title="Yard", start_position=[0.5, 0.0, 0.0], north_offset=1.5)
        ArticleMedia.objects.create(article=self.article, media_type="panorama", panorama=panorama)
        media = self.get(id=self.article.pk)[0]["advanced_media"]
        assert media["start_position"] == [0.5, 0.0, 0.0]
        assert media["north_offset"] == 1.5
        assert media["uuid"] == str(panorama.uuid)
        assert "technique" not in media


@pytest.mark.django_db
class TestArticleMediaTypeFilter:
    """?media_type= on /api/articles/ and /api/article_info/"""

    def setup_method(self):
        self.client = APIClient()
        self.panorama_article = Article.objects.create(title="Gården")
        ArticleMedia.objects.create(article=self.panorama_article, media_type="panorama",
                                    panorama=Panorama.objects.create(title="Yard"))
        self.cloud_article = Article.objects.create(title="Smedjan")
        ArticleMedia.objects.create(article=self.cloud_article, media_type="pointcloud",
                                    pointcloud=PointCloud.objects.create(title="Scan"))
        self.plain_article = Article.objects.create(title="Dammen")

    def ids(self, endpoint, media_type):
        response = self.client.get(f"/sv/api/{endpoint}/", {"media_type": media_type})
        assert response.status_code == status.HTTP_200_OK
        return {r["id"] for r in response.data["results"]}

    @pytest.mark.parametrize("endpoint", ["articles", "article_info"])
    def test_filter_one_type(self, endpoint):
        assert self.ids(endpoint, "panorama") == {self.panorama_article.pk}

    def test_filter_several_types(self):
        assert self.ids("articles", "panorama,pointcloud") == {self.panorama_article.pk, self.cloud_article.pk}

    def test_deleted_resource_is_not_matched(self):
        self.panorama_article.advanced_media.panorama.delete()
        assert self.ids("articles", "panorama") == set()

    def test_unknown_type_is_rejected(self):
        assert self.client.get("/sv/api/articles/", {"media_type": "video"}).status_code == status.HTTP_400_BAD_REQUEST
