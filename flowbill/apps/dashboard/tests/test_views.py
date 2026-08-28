import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework.test import APIClient
from tests.factories import UserFactory, ClientFactory, InvoiceFactory


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


@pytest.mark.django_db
class TestDashboardStatsView:
    """Tests for GET /api/v1/dashboard/stats/"""

    url = "/api/v1/dashboard/stats/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_authenticated_returns_200(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        assert response.status_code == 200

    def test_response_has_correct_shape(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        data = response.data["data"]
        assert "total_earned" in data
        assert "total_pending" in data
        assert "total_overdue" in data
        assert "active_clients" in data
        assert "pending_count" in data
        assert "overdue_count" in data

    def test_total_earned_counts_paid_invoices_only(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        InvoiceFactory(owner=user, client=my_client, status="paid", total=Decimal("1000.00"))
        InvoiceFactory(owner=user, client=my_client, status="paid", total=Decimal("2000.00"))
        InvoiceFactory(owner=user, client=my_client, status="pending", total=Decimal("500.00"))
        response = api_client.get(self.url)
        assert Decimal(response.data["data"]["total_earned"]) == Decimal("3000.00")

    def test_total_pending_counts_pending_invoices_only(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        InvoiceFactory(owner=user, client=my_client, status="pending", total=Decimal("1500.00"))
        InvoiceFactory(owner=user, client=my_client, status="pending", total=Decimal("2500.00"))
        InvoiceFactory(owner=user, client=my_client, status="paid", total=Decimal("1000.00"))
        response = api_client.get(self.url)
        assert Decimal(response.data["data"]["total_pending"]) == Decimal("4000.00")

    def test_total_overdue_counts_overdue_invoices_only(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        InvoiceFactory(owner=user, client=my_client, status="overdue", total=Decimal("800.00"))
        InvoiceFactory(owner=user, client=my_client, status="overdue", total=Decimal("600.00"))
        InvoiceFactory(owner=user, client=my_client, status="paid", total=Decimal("1000.00"))
        response = api_client.get(self.url)
        assert Decimal(response.data["data"]["total_overdue"]) == Decimal("1400.00")

    def test_active_clients_count(self, auth_client):
        api_client, user = auth_client
        ClientFactory.create_batch(4, owner=user, status="active")
        ClientFactory(owner=user, status="inactive")
        response = api_client.get(self.url)
        assert response.data["data"]["active_clients"] == 4

    def test_stats_only_include_own_data(self, auth_client):
        api_client, user = auth_client
        other_user = UserFactory()
        other_client = ClientFactory(owner=other_user)
        InvoiceFactory(owner=other_user, client=other_client, status="paid", total=Decimal("9999.00"))
        my_client = ClientFactory(owner=user)
        InvoiceFactory(owner=user, client=my_client, status="paid", total=Decimal("100.00"))
        response = api_client.get(self.url)
        assert Decimal(response.data["data"]["total_earned"]) == Decimal("100.00")

    def test_empty_dashboard_returns_zeros(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        data = response.data["data"]
        assert Decimal(data["total_earned"]) == Decimal("0.00")
        assert Decimal(data["total_pending"]) == Decimal("0.00")
        assert Decimal(data["total_overdue"]) == Decimal("0.00")
        assert data["active_clients"] == 0


@pytest.mark.django_db
class TestRevenueChartView:
    """Tests for GET /api/v1/dashboard/revenue-chart/"""

    url = "/api/v1/dashboard/revenue-chart/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_authenticated_returns_200(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        assert response.status_code == 200

    def test_response_has_labels_and_data(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        data = response.data["data"]
        assert "labels" in data
        assert "data" in data

    def test_default_returns_6_months(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        assert len(response.data["data"]["labels"]) == 6
        assert len(response.data["data"]["data"]) == 6

    def test_custom_months_param(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(f"{self.url}?months=3")
        assert len(response.data["data"]["labels"]) == 3

    def test_months_param_capped_at_12(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(f"{self.url}?months=24")
        assert len(response.data["data"]["labels"]) <= 12

    def test_only_counts_paid_invoices(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        InvoiceFactory(
            owner=user, client=my_client,
            status="paid", total=Decimal("1000.00"),
            issue_date=date.today(),
        )
        InvoiceFactory(
            owner=user, client=my_client,
            status="pending", total=Decimal("9999.00"),
            issue_date=date.today(),
        )
        response = api_client.get(self.url)
        current_month_total = response.data["data"]["data"][-1]
        assert Decimal(str(current_month_total)) == Decimal("1000.00")


@pytest.mark.django_db
class TestTopClientsView:
    """Tests for GET /api/v1/dashboard/top-clients/"""

    url = "/api/v1/dashboard/top-clients/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_authenticated_returns_200(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        assert response.status_code == 200

    def test_returns_clients_sorted_by_total_billed(self, auth_client):
        api_client, user = auth_client
        client1 = ClientFactory(owner=user)
        client2 = ClientFactory(owner=user)
        InvoiceFactory(owner=user, client=client1, status="paid", total=Decimal("500.00"))
        InvoiceFactory(owner=user, client=client2, status="paid", total=Decimal("2000.00"))
        response = api_client.get(self.url)
        data = response.data["data"]
        assert Decimal(data[0]["total_billed"]) >= Decimal(data[1]["total_billed"])

    def test_default_limit_is_5(self, auth_client):
        api_client, user = auth_client
        clients = ClientFactory.create_batch(7, owner=user)
        for c in clients:
            InvoiceFactory(owner=user, client=c, status="paid", total=Decimal("100.00"))
        response = api_client.get(self.url)
        assert len(response.data["data"]) <= 5

    def test_response_has_correct_fields(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        InvoiceFactory(owner=user, client=my_client, status="paid", total=Decimal("1000.00"))
        response = api_client.get(self.url)
        if response.data["data"]:
            item = response.data["data"][0]
            assert "client_id" in item
            assert "name" in item
            assert "total_billed" in item
            assert "invoice_count" in item

    def test_only_includes_own_clients(self, auth_client):
        api_client, user = auth_client
        other_user = UserFactory()
        other_client = ClientFactory(owner=other_user)
        InvoiceFactory(owner=other_user, client=other_client, status="paid", total=Decimal("9999.00"))
        response = api_client.get(self.url)
        assert response.data["data"] == []


@pytest.mark.django_db
class TestUpcomingDueView:
    """Tests for GET /api/v1/dashboard/upcoming-due/"""

    url = "/api/v1/dashboard/upcoming-due/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_authenticated_returns_200(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        assert response.status_code == 200

    def test_returns_invoices_due_within_7_days(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        InvoiceFactory(
            owner=user, client=my_client,
            status="pending",
            due_date=date.today() + timedelta(days=3),
        )
        InvoiceFactory(
            owner=user, client=my_client,
            status="pending",
            due_date=date.today() + timedelta(days=30),
        )
        response = api_client.get(self.url)
        assert len(response.data["data"]) == 1

    def test_excludes_paid_invoices(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        InvoiceFactory(
            owner=user, client=my_client,
            status="paid",
            due_date=date.today() + timedelta(days=2),
        )
        response = api_client.get(self.url)
        assert len(response.data["data"]) == 0

    def test_response_has_correct_fields(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        InvoiceFactory(
            owner=user, client=my_client,
            status="pending",
            due_date=date.today() + timedelta(days=2),
        )
        response = api_client.get(self.url)
        if response.data["data"]:
            item = response.data["data"][0]
            assert "invoice_id" in item
            assert "number" in item
            assert "client_name" in item
            assert "amount" in item
            assert "due_date" in item
            assert "days_until_due" in item