import pytest
from decimal import Decimal
from datetime import date
from rest_framework.test import APIClient
from tests.factories import UserFactory, ClientFactory, ExpenseFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(db):
    user = UserFactory()
    client = APIClient()
    response = client.post("/api/v1/auth/login/", {
        "email": user.email,
        "password": "SecurePass123!",
    }, format="json")
    token = response.data["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client, user


def get_valid_payload():
    return {
        "amount": "15000.00",
        "currency": "NGN",
        "category": "software",
        "description": "Figma annual subscription",
        "date": str(date.today()),
        "notes": "Design tool",
    }


@pytest.mark.django_db
class TestExpenseListCreateView:
    """Tests for GET/POST /api/v1/expenses/"""

    url = "/api/v1/expenses/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_authenticated_can_list_expenses(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        assert response.status_code == 200

    def test_list_returns_only_own_expenses(self, auth_client):
        api_client, user = auth_client
        other_user = UserFactory()
        ExpenseFactory.create_batch(3, owner=user)
        ExpenseFactory.create_batch(2, owner=other_user)
        response = api_client.get(self.url)
        assert response.data["meta"]["total"] == 3

    def test_create_expense_returns_201(self, auth_client):
        api_client, user = auth_client
        response = api_client.post(self.url, get_valid_payload(), format="json")
        assert response.status_code == 201

    def test_create_expense_sets_owner(self, auth_client):
        from apps.expenses.models import Expense
        api_client, user = auth_client
        api_client.post(self.url, get_valid_payload(), format="json")
        expense = Expense.objects.get(description="Figma annual subscription")
        assert expense.owner == user

    def test_create_expense_response_shape(self, auth_client):
        api_client, user = auth_client
        response = api_client.post(self.url, get_valid_payload(), format="json")
        assert response.data["status"] == "success"
        assert "data" in response.data

    def test_list_excludes_soft_deleted(self, auth_client):
        api_client, user = auth_client
        ExpenseFactory.create_batch(3, owner=user)
        deleted = ExpenseFactory(owner=user)
        deleted.delete()
        response = api_client.get(self.url)
        assert response.data["meta"]["total"] == 3

    def test_filter_by_category(self, auth_client):
        api_client, user = auth_client
        ExpenseFactory.create_batch(2, owner=user, category="software")
        ExpenseFactory(owner=user, category="travel")
        response = api_client.get(f"{self.url}?category=software")
        assert response.data["meta"]["total"] == 2

    def test_list_response_has_correct_shape(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        assert response.data["status"] == "success"
        assert "meta" in response.data
        assert "data" in response.data

    def test_invalid_payload_returns_400(self, auth_client):
        api_client, user = auth_client
        response = api_client.post(self.url, {"amount": "-100"}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestExpenseRetrieveUpdateDeleteView:
    """Tests for GET/PATCH/DELETE /api/v1/expenses/{id}/"""

    def get_url(self, expense_id):
        return f"/api/v1/expenses/{expense_id}/"

    def test_retrieve_own_expense_returns_200(self, auth_client):
        api_client, user = auth_client
        expense = ExpenseFactory(owner=user)
        response = api_client.get(self.get_url(expense.id))
        assert response.status_code == 200

    def test_cannot_retrieve_another_users_expense(self, auth_client):
        api_client, user = auth_client
        other_user = UserFactory()
        expense = ExpenseFactory(owner=other_user)
        response = api_client.get(self.get_url(expense.id))
        assert response.status_code == 404

    def test_update_expense_returns_200(self, auth_client):
        api_client, user = auth_client
        expense = ExpenseFactory(owner=user)
        response = api_client.patch(
            self.get_url(expense.id),
            {"description": "Updated description"},
            format="json"
        )
        assert response.status_code == 200

    def test_cannot_update_another_users_expense(self, auth_client):
        api_client, user = auth_client
        other_user = UserFactory()
        expense = ExpenseFactory(owner=other_user)
        response = api_client.patch(
            self.get_url(expense.id),
            {"description": "Hacked"},
            format="json"
        )
        assert response.status_code == 404

    def test_delete_expense_returns_200(self, auth_client):
        api_client, user = auth_client
        expense = ExpenseFactory(owner=user)
        response = api_client.delete(self.get_url(expense.id))
        assert response.status_code == 200

    def test_delete_is_soft_delete(self, auth_client):
        from apps.expenses.models import Expense
        api_client, user = auth_client
        expense = ExpenseFactory(owner=user)
        api_client.delete(self.get_url(expense.id))
        db_expense = Expense.objects.get(id=expense.id)
        assert db_expense.is_deleted is True

    def test_cannot_delete_another_users_expense(self, auth_client):
        api_client, user = auth_client
        other_user = UserFactory()
        expense = ExpenseFactory(owner=other_user)
        response = api_client.delete(self.get_url(expense.id))
        assert response.status_code == 404

    def test_retrieve_returns_correct_data(self, auth_client):
        api_client, user = auth_client
        expense = ExpenseFactory(owner=user, description="Figma subscription")
        response = api_client.get(self.get_url(expense.id))
        assert response.data["data"]["description"] == "Figma subscription"