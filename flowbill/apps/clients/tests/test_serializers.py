import pytest
from tests.factories import UserFactory, ClientFactory
from apps.clients.serializers import ClientSerializer


@pytest.mark.django_db
class TestClientSerializer:
    """Tests for ClientSerializer."""

    def get_valid_data(self):
        return {
            "name": "Tunde Adeyemi",
            "email": "tunde@example.com",
            "phone": "+2348012345678",
            "company_name": "Pixel Studio Ltd",
            "website": "https://pixelstudio.com",
            "address": "12 Allen Avenue",
            "city": "Lagos",
            "state": "Lagos",
            "country": "NG",
            "currency": "NGN",
            "notes": "Preferred contact via email",
        }

    def test_valid_data_passes(self):
        serializer = ClientSerializer(data=self.get_valid_data())
        assert serializer.is_valid(), serializer.errors

    def test_only_name_and_email_are_required(self):
        serializer = ClientSerializer(data={
            "name": "Tunde Adeyemi",
            "email": "tunde@example.com",
        })
        assert serializer.is_valid(), serializer.errors

    def test_missing_name_fails(self):
        data = self.get_valid_data()
        del data["name"]
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_missing_email_fails(self):
        data = self.get_valid_data()
        del data["email"]
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_invalid_email_fails(self):
        data = self.get_valid_data()
        data["email"] = "not-an-email"
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_invalid_currency_fails(self):
        data = self.get_valid_data()
        data["currency"] = "INVALID"
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "currency" in serializer.errors

    def test_invalid_country_code_fails(self):
        data = self.get_valid_data()
        data["country"] = "INVALID"
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "country" in serializer.errors

    def test_owner_field_not_in_serializer_input(self):
        """Owner should be set by the view, not the client."""
        data = self.get_valid_data()
        data["owner"] = "some-uuid"
        serializer = ClientSerializer(data=data)
        assert serializer.is_valid()
        assert "owner" not in serializer.validated_data

    def test_serializer_output_includes_id(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        serializer = ClientSerializer(client)
        assert "id" in serializer.data

    def test_serializer_output_excludes_is_deleted(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        serializer = ClientSerializer(client)
        assert "is_deleted" not in serializer.data

    def test_website_must_be_valid_url(self):
        data = self.get_valid_data()
        data["website"] = "not-a-url"
        serializer = ClientSerializer(data=data)
        assert not serializer.is_valid()
        assert "website" in serializer.errors

    def test_website_can_be_blank(self):
        data = self.get_valid_data()
        data["website"] = ""
        serializer = ClientSerializer(data=data)
        assert serializer.is_valid(), serializer.errors