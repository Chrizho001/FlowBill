import pytest
from rest_framework.test import APIClient
from tests.factories import UserFactory, ClientFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(db):
    user = UserFactory()
    client = APIClient()
    # Get JWT token
    response = client.post("/api/v1/auth/login/", {
        "email": user.email,
        "password": "SecurePass123!",
    }, format="json")
    token = response.data["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client, user


@pytest.mark.django_db
class TestClientListCreateView:
    """Tests for GET/POST /api/v1/clients/"""

    url = "/api/v1/clients/"

    def get_valid_payload(self):
        return {
            "name": "Tunde Adeyemi",
            "email": "tunde@example.com",
            "company_name": "Pixel Studio",
            "currency": "NGN",
            "country": "NG",
        }

    def test_unauthenticated_request_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_authenticated_user_can_list_clients(self, auth_client):
        client, user = auth_client
        ClientFactory.create_batch(3, owner=user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_list_returns_only_own_clients(self, auth_client):
        client, user = auth_client
        other_user = UserFactory()
        ClientFactory.create_batch(3, owner=user)
        ClientFactory.create_batch(2, owner=other_user)
        response = client.get(self.url)
        assert response.data["meta"]["total"] == 3

    def test_create_client_returns_201(self, auth_client):
        client, user = auth_client
        response = client.post(self.url, self.get_valid_payload(), format="json")
        assert response.status_code == 201

    def test_create_client_sets_owner_to_current_user(self, auth_client):
        from apps.clients.models import Client
        client, user = auth_client
        client.post(self.url, self.get_valid_payload(), format="json")
        created = Client.objects.get(email="tunde@example.com")
        assert created.owner == user

    def test_create_duplicate_email_same_owner_returns_400(self, auth_client):
        client, user = auth_client
        ClientFactory(owner=user, email="tunde@example.com")
        response = client.post(self.url, self.get_valid_payload(), format="json")
        assert response.status_code == 400

    def test_create_duplicate_email_different_owner_returns_201(self, auth_client):
        client, user = auth_client
        other_user = UserFactory()
        ClientFactory(owner=other_user, email="tunde@example.com")
        response = client.post(self.url, self.get_valid_payload(), format="json")
        assert response.status_code == 201

    def test_list_excludes_soft_deleted_clients(self, auth_client):
        client, user = auth_client
        active = ClientFactory.create_batch(3, owner=user)
        deleted = ClientFactory(owner=user)
        deleted.delete()
        response = client.get(self.url)
        assert response.data["meta"]["total"] == 3

    def test_list_response_has_correct_shape(self, auth_client):
        client, user = auth_client
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert "meta" in response.data
        assert "data" in response.data

    def test_search_clients_by_name(self, auth_client):
        client, user = auth_client
        ClientFactory(owner=user, name="Tunde Adeyemi")
        ClientFactory(owner=user, name="Sarah Johnson")
        response = client.get(f"{self.url}?search=Tunde")
        assert response.data["meta"]["total"] == 1

    def test_filter_clients_by_status(self, auth_client):
        client, user = auth_client
        ClientFactory.create_batch(2, owner=user, status="active")
        ClientFactory(owner=user, status="inactive")
        response = client.get(f"{self.url}?status=active")
        assert response.data["meta"]["total"] == 2


@pytest.mark.django_db
class TestClientRetrieveUpdateDeleteView:
    """Tests for GET/PUT/DELETE /api/v1/clients/{id}/"""

    def get_url(self, client_id):
        return f"/api/v1/clients/{client_id}/"

    def test_retrieve_own_client_returns_200(self, auth_client):
        client, user = auth_client
        my_client = ClientFactory(owner=user)
        response = client.get(self.get_url(my_client.id))
        assert response.status_code == 200

    def test_cannot_retrieve_another_users_client(self, auth_client):
        client, user = auth_client
        other_user = UserFactory()
        their_client = ClientFactory(owner=other_user)
        response = client.get(self.get_url(their_client.id))
        assert response.status_code == 404

    def test_update_own_client_returns_200(self, auth_client):
        client, user = auth_client
        my_client = ClientFactory(owner=user)
        response = client.patch(self.get_url(my_client.id), {
            "name": "Updated Name"
        }, format="json")
        assert response.status_code == 200

    def test_cannot_update_another_users_client(self, auth_client):
        client, user = auth_client
        other_user = UserFactory()
        their_client = ClientFactory(owner=other_user)
        response = client.patch(self.get_url(their_client.id), {
            "name": "Hacked"
        }, format="json")
        assert response.status_code == 404

    def test_delete_client_returns_200(self, auth_client):
        client, user = auth_client
        my_client = ClientFactory(owner=user)
        response = client.delete(self.get_url(my_client.id))
        assert response.status_code == 200

    def test_delete_is_soft_delete(self, auth_client):
        from apps.clients.models import Client
        client, user = auth_client
        my_client = ClientFactory(owner=user)
        client.delete(self.get_url(my_client.id))
        db_client = Client.objects.get(id=my_client.id)
        assert db_client.is_deleted is True

    def test_cannot_delete_another_users_client(self, auth_client):
        client, user = auth_client
        other_user = UserFactory()
        their_client = ClientFactory(owner=other_user)
        response = client.delete(self.get_url(their_client.id))
        assert response.status_code == 404

    def test_retrieve_returns_client_data(self, auth_client):
        client, user = auth_client
        my_client = ClientFactory(owner=user, name="Tunde Adeyemi")
        response = client.get(self.get_url(my_client.id))
        assert response.data["data"]["name"] == "Tunde Adeyemi"