"""
Business logo upload: POST/DELETE /api/v1/auth/profile/logo/

Logos are uploaded (never hot-linked by URL), validated, re-encoded to PNG
(metadata stripped, max 600px) and stored, so invoice PDFs can embed them
without any network access at render time.
"""

import io

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import BusinessProfile
from tests.factories import UserFactory

URL = "/api/v1/auth/profile/logo/"


def image_file(fmt="PNG", size=(1200, 300), name=None, exif=False, color=(242, 84, 91)):
    buf = io.BytesIO()
    img = Image.new("RGB", size, color)
    kwargs = {}
    if exif:
        ex = Image.Exif()
        ex[0x010F] = "SecretCameraMaker"  # Make
        ex[0x0132] = "2026:01:01 10:00:00"  # DateTime
        kwargs["exif"] = ex.tobytes()
    img.save(buf, format=fmt, **kwargs)
    ext = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp", "GIF": "gif"}[fmt]
    return SimpleUploadedFile(name or f"logo.{ext}", buf.getvalue(), content_type=f"image/{ext}")


@pytest.fixture(autouse=True)
def media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def user(db):
    u = UserFactory()
    BusinessProfile.objects.get_or_create(user=u)
    return u


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def stored_image(user):
    profile = BusinessProfile.objects.get(user=user)
    with default_storage.open(profile.logo.name, "rb") as fh:
        img = Image.open(io.BytesIO(fh.read()))
        img.load()
    return profile, img


@pytest.mark.django_db
class TestLogoUpload:
    def test_png_upload_is_resized_and_stored_as_png(self, client, user):
        res = client.post(URL, {"logo": image_file("PNG", (1200, 300))}, format="multipart")

        assert res.status_code == 200
        assert res.json()["data"]["logo_url"].endswith(".png")
        profile, img = stored_image(user)
        assert img.format == "PNG"
        assert max(img.size) == 600 and img.size == (600, 150)

    @pytest.mark.parametrize("fmt", ["JPEG", "WEBP"])
    def test_jpeg_and_webp_are_accepted_and_reencoded_to_png(self, client, user, fmt):
        res = client.post(URL, {"logo": image_file(fmt, (300, 300))}, format="multipart")

        assert res.status_code == 200
        _, img = stored_image(user)
        assert img.format == "PNG"

    def test_metadata_is_stripped(self, client, user):
        res = client.post(URL, {"logo": image_file("JPEG", (400, 400), exif=True)}, format="multipart")

        assert res.status_code == 200
        _, img = stored_image(user)
        assert not img.getexif()
        assert "exif" not in img.info

    def test_svg_is_rejected(self, client):
        svg = SimpleUploadedFile(
            "logo.svg",
            b'<svg xmlns="http://www.w3.org/2000/svg"><image href="http://169.254.169.254/"/></svg>',
            content_type="image/svg+xml",
        )
        res = client.post(URL, {"logo": svg}, format="multipart")

        assert res.status_code == 400
        assert "logo" in res.json()["fields"]

    def test_gif_is_rejected(self, client):
        res = client.post(URL, {"logo": image_file("GIF", (100, 100))}, format="multipart")

        assert res.status_code == 400
        assert "logo" in res.json()["fields"]

    def test_non_image_disguised_as_png_is_rejected(self, client):
        fake = SimpleUploadedFile("logo.png", b"not really an image", content_type="image/png")
        res = client.post(URL, {"logo": fake}, format="multipart")

        assert res.status_code == 400
        assert "logo" in res.json()["fields"]

    def test_file_over_one_megabyte_is_rejected(self, client, settings):
        settings.LOGO_MAX_UPLOAD_BYTES = 1024  # keep the test fast
        res = client.post(URL, {"logo": image_file("PNG", (400, 400))}, format="multipart")

        assert res.status_code == 400
        assert "logo" in res.json()["fields"]

    def test_oversized_dimensions_are_rejected_before_decoding(self, client, settings):
        settings.LOGO_MAX_SOURCE_PIXELS = 1000 * 1000
        res = client.post(URL, {"logo": image_file("PNG", (2000, 2000))}, format="multipart")

        assert res.status_code == 400
        assert "logo" in res.json()["fields"]

    def test_missing_file_is_rejected(self, client):
        res = client.post(URL, {}, format="multipart")

        assert res.status_code == 400
        assert "logo" in res.json()["fields"]

    def test_replacing_a_logo_deletes_the_old_file(self, client, user):
        client.post(URL, {"logo": image_file("PNG", (200, 200))}, format="multipart")
        old_name = BusinessProfile.objects.get(user=user).logo.name

        client.post(URL, {"logo": image_file("PNG", (300, 300), color=(0, 0, 0))}, format="multipart")
        new_name = BusinessProfile.objects.get(user=user).logo.name

        assert new_name != old_name
        assert not default_storage.exists(old_name)
        assert default_storage.exists(new_name)

    def test_delete_removes_logo_and_file(self, client, user):
        client.post(URL, {"logo": image_file("PNG", (200, 200))}, format="multipart")
        name = BusinessProfile.objects.get(user=user).logo.name

        res = client.delete(URL)

        assert res.status_code == 200
        assert res.json()["data"]["logo_url"] is None
        assert not BusinessProfile.objects.get(user=user).logo
        assert not default_storage.exists(name)

    def test_requires_authentication(self, db):
        res = APIClient().post(URL, {"logo": image_file()}, format="multipart")
        assert res.status_code == 401

    def test_logo_url_is_no_longer_writable_through_profile_update(self, client, user):
        res = client.patch(
            "/api/v1/auth/profile/",
            {"logo_url": "http://169.254.169.254/latest/meta-data/"},
            format="json",
        )

        assert res.status_code == 200
        assert res.json()["data"]["logo_url"] is None
        assert not BusinessProfile.objects.get(user=user).logo
