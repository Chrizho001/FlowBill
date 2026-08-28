import pytest
from django.contrib.auth import get_user_model
from tests.factories import UserFactory, ClientFactory

User = get_user_model()


@pytest.mark.django_db
class TestClientModel:
    """Tests for the Client model."""

    def test_create_client_with_required_fields(self):
        user = UserFactory()
        client = ClientFactory(owner=user, name="Tunde Adeyemi", email="tunde@example.com")
        assert client.name == "Tunde Adeyemi"
        assert client.email == "tunde@example.com"
        assert client.owner == user

    def test_client_status_defaults_to_active(self):
        client = ClientFactory()
        assert client.status == "active"

    def test_client_is_not_deleted_by_default(self):
        client = ClientFactory()
        assert client.is_deleted is False
        assert client.deleted_at is None

    def test_client_soft_delete(self):
        client = ClientFactory()
        client.delete()
        assert client.is_deleted is True
        assert client.deleted_at is not None

    def test_soft_deleted_client_still_exists_in_db(self):
        from apps.clients.models import Client
        client = ClientFactory()
        client_id = client.id
        client.delete()
        assert Client.objects.filter(id=client_id).exists()

    def test_client_restore_after_soft_delete(self):
        client = ClientFactory()
        client.delete()
        assert client.is_deleted is True
        client.restore()
        assert client.is_deleted is False
        assert client.deleted_at is None

    def test_client_str_returns_name_and_company(self):
        client = ClientFactory(name="Tunde Adeyemi", company_name="Pixel Studio")
        assert "Tunde Adeyemi" in str(client)

    def test_client_str_without_company(self):
        client = ClientFactory(name="Tunde Adeyemi", company_name="")
        assert str(client) == "Tunde Adeyemi"

    def test_client_id_is_uuid(self):
        import uuid
        client = ClientFactory()
        assert isinstance(client.id, uuid.UUID)

    def test_two_clients_same_owner_cannot_share_email(self):
        from django.db import IntegrityError
        user = UserFactory()
        ClientFactory(owner=user, email="shared@example.com")
        with pytest.raises(IntegrityError):
            ClientFactory(owner=user, email="shared@example.com")

    def test_two_clients_different_owners_can_share_email(self):
        """Same email is allowed across different owners."""
        from apps.clients.models import Client
        user1 = UserFactory()
        user2 = UserFactory()
        ClientFactory(owner=user1, email="shared@example.com")
        ClientFactory(owner=user2, email="shared@example.com")
        assert Client.objects.filter(email="shared@example.com").count() == 2

    def test_client_belongs_to_owner(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        assert client.owner.id == user.id

    def test_client_currency_defaults_to_usd(self):
        client = ClientFactory()
        assert client.currency == "USD"