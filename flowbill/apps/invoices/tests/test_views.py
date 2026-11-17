import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework.test import APIClient
from tests.factories import UserFactory, ClientFactory, InvoiceFactory, LineItemFactory


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


@pytest.fixture
def client_with_client(auth_client):
    api_client, user = auth_client
    my_client = ClientFactory(owner=user)
    return api_client, user, my_client


def get_invoice_payload(client_id):
    return {
        "client": str(client_id),
        "issue_date": str(date.today()),
        "due_date": str(date.today() + timedelta(days=30)),
        "currency": "USD",
        "payment_terms": "net_30",
        "notes": "Payment due within 30 days.",
        "discount_amount": "0.00",
        "line_items": [
            {
                "description": "UI Design",
                "quantity": "1.00",
                "unit_price": "1000.00",
                "tax_rate": "0.00",
            },
        ],
    }


@pytest.mark.django_db
class TestInvoiceListCreateView:
    """Tests for GET/POST /api/v1/invoices/"""

    url = "/api/v1/invoices/"

    def test_unauthenticated_request_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_authenticated_user_can_list_invoices(self, auth_client):
        api_client, user = auth_client
        response = api_client.get(self.url)
        assert response.status_code == 200

    def test_list_returns_only_own_invoices(self, auth_client):
        api_client, user = auth_client
        other_user = UserFactory()
        other_client = ClientFactory(owner=other_user)
        my_client = ClientFactory(owner=user)
        InvoiceFactory.create_batch(3, owner=user, client=my_client)
        InvoiceFactory.create_batch(2, owner=other_user, client=other_client)
        response = api_client.get(self.url)
        assert response.data["meta"]["total"] == 3

    def test_create_invoice_returns_201(self, client_with_client):
        api_client, user, my_client = client_with_client
        response = api_client.post(
            self.url,
            get_invoice_payload(my_client.id),
            format="json"
        )
        assert response.status_code == 201

    def test_create_invoice_generates_number(self, client_with_client):
        api_client, user, my_client = client_with_client
        response = api_client.post(
            self.url,
            get_invoice_payload(my_client.id),
            format="json"
        )
        assert response.status_code == 201
        number = response.data["data"]["number"]
        assert number.startswith(f"INV-{date.today().year}-")

    def test_create_invoice_calculates_totals(self, client_with_client):
        api_client, user, my_client = client_with_client
        response = api_client.post(
            self.url,
            get_invoice_payload(my_client.id),
            format="json"
        )
        assert response.status_code == 201
        assert Decimal(response.data["data"]["subtotal"]) == Decimal("1000.00")
        assert Decimal(response.data["data"]["total"]) == Decimal("1000.00")

    def test_create_invoice_status_is_draft(self, client_with_client):
        api_client, user, my_client = client_with_client
        response = api_client.post(
            self.url,
            get_invoice_payload(my_client.id),
            format="json"
        )
        assert response.data["data"]["status"] == "draft"

    def test_create_invoice_with_another_users_client_fails(self, auth_client):
        api_client, user = auth_client
        other_user = UserFactory()
        other_client = ClientFactory(owner=other_user)
        response = api_client.post(
            self.url,
            get_invoice_payload(other_client.id),
            format="json"
        )
        assert response.status_code == 400

    def test_create_invoice_without_line_items_fails(self, client_with_client):
        api_client, user, my_client = client_with_client
        payload = get_invoice_payload(my_client.id)
        payload["line_items"] = []
        response = api_client.post(self.url, payload, format="json")
        assert response.status_code == 400

    def test_filter_invoices_by_status(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        InvoiceFactory.create_batch(2, owner=user, client=my_client, status="draft")
        InvoiceFactory(owner=user, client=my_client, status="pending")
        response = api_client.get(f"{self.url}?status=draft")
        assert response.data["meta"]["total"] == 2

    def test_filter_invoices_by_client(self, auth_client):
        api_client, user = auth_client
        client1 = ClientFactory(owner=user)
        client2 = ClientFactory(owner=user)
        InvoiceFactory.create_batch(2, owner=user, client=client1)
        InvoiceFactory(owner=user, client=client2)
        response = api_client.get(f"{self.url}?client={client1.id}")
        assert response.data["meta"]["total"] == 2


@pytest.mark.django_db
class TestInvoiceRetrieveUpdateDeleteView:
    """Tests for GET/PATCH/DELETE /api/v1/invoices/{id}/"""

    def get_url(self, invoice_id):
        return f"/api/v1/invoices/{invoice_id}/"

    def test_retrieve_own_invoice_returns_200(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client)
        response = api_client.get(self.get_url(invoice.id))
        assert response.status_code == 200

    def test_cannot_retrieve_another_users_invoice(self, auth_client):
        api_client, user = auth_client
        other_user = UserFactory()
        other_client = ClientFactory(owner=other_user)
        invoice = InvoiceFactory(owner=other_user, client=other_client)
        response = api_client.get(self.get_url(invoice.id))
        assert response.status_code == 404

    def test_retrieve_includes_line_items(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client)
        LineItemFactory.create_batch(3, invoice=invoice)
        response = api_client.get(self.get_url(invoice.id))
        assert len(response.data["data"]["line_items"]) == 3

    def test_retrieve_includes_events(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client)
        response = api_client.get(self.get_url(invoice.id))
        assert "events" in response.data["data"]

    def test_update_draft_invoice_returns_200(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client, status="draft")
        response = api_client.patch(
            self.get_url(invoice.id),
            {"notes": "Updated notes"},
            format="json"
        )
        assert response.status_code == 200

    def test_cannot_update_pending_invoice(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client, status="pending")
        response = api_client.patch(
            self.get_url(invoice.id),
            {"notes": "Updated notes"},
            format="json"
        )
        assert response.status_code == 400

    def test_cancel_draft_invoice_returns_200(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client, status="draft")
        response = api_client.delete(self.get_url(invoice.id))
        assert response.status_code == 200

    def test_cancel_sets_status_to_cancelled(self, auth_client):
        from apps.invoices.models import Invoice
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client, status="draft")
        api_client.delete(self.get_url(invoice.id))
        updated = Invoice.objects.get(id=invoice.id)
        assert updated.status == "cancelled"


@pytest.mark.django_db
class TestInvoiceActionsView:
    """Tests for invoice action endpoints."""

    def test_send_invoice_changes_status_to_pending(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client, status="draft")
        response = api_client.post(f"/api/v1/invoices/{invoice.id}/send/")
        assert response.status_code == 200
        from apps.invoices.models import Invoice
        updated = Invoice.objects.get(id=invoice.id)
        assert updated.status == "pending"

    def test_cannot_send_already_sent_invoice(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client, status="pending")
        response = api_client.post(f"/api/v1/invoices/{invoice.id}/send/")
        assert response.status_code == 400

    def test_mark_paid_changes_status(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client, status="pending")
        response = api_client.post(
            f"/api/v1/invoices/{invoice.id}/mark-paid/",
            {"paid_at": str(date.today()), "amount": "1000.00"},
            format="json"
        )
        assert response.status_code == 200
        from apps.invoices.models import Invoice
        updated = Invoice.objects.get(id=invoice.id)
        assert updated.status == "paid"

    def test_mark_paid_with_mismatched_amount_fails(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client, status="pending", total=Decimal("1000.00"))
        response = api_client.post(
            f"/api/v1/invoices/{invoice.id}/mark-paid/",
            {"paid_at": str(date.today()), "amount": "50.00"},
            format="json"
        )
        assert response.status_code == 400
        assert "amount" in response.json()["fields"]

    def test_discount_exceeding_total_fails(self, client_with_client):
        api_client, user, my_client = client_with_client
        payload = get_invoice_payload(my_client.id)
        payload["discount_amount"] = "2500.00"
        response = api_client.post("/api/v1/invoices/", payload, format="json")
        assert response.status_code == 400
        assert "discount_amount" in response.json()["fields"]

    def test_update_invoice_client_ownership_validated(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        my_second_client = ClientFactory(owner=user)
        other_client = ClientFactory(owner=UserFactory())
        invoice = InvoiceFactory(owner=user, client=my_client, status="draft")

        # Reassigning to another user's client fails with 400
        bad_res = api_client.patch(
            f"/api/v1/invoices/{invoice.id}/",
            {"client": str(other_client.id)},
            format="json",
        )
        assert bad_res.status_code == 400

        # Reassigning to own second client succeeds
        ok_res = api_client.patch(
            f"/api/v1/invoices/{invoice.id}/",
            {"client": str(my_second_client.id)},
            format="json",
        )
        assert ok_res.status_code == 200
        invoice.refresh_from_db()
        assert invoice.client_id == my_second_client.id

    def test_duplicate_invoice_creates_new_draft(self, auth_client):
        api_client, user = auth_client
        my_client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=my_client, status="pending")
        LineItemFactory.create_batch(2, invoice=invoice)
        response = api_client.post(f"/api/v1/invoices/{invoice.id}/duplicate/")
        assert response.status_code == 201
        from apps.invoices.models import Invoice
        assert Invoice.objects.filter(owner=user).count() == 2
        new_invoice = Invoice.objects.exclude(id=invoice.id).get(owner=user)
        assert new_invoice.status == "draft"
        assert new_invoice.number != invoice.number