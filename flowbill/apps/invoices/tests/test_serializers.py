import pytest
from decimal import Decimal
from datetime import date, timedelta
from tests.factories import UserFactory, ClientFactory, InvoiceFactory, LineItemFactory
from apps.invoices.serializers import InvoiceSerializer, LineItemSerializer


@pytest.mark.django_db
class TestLineItemSerializer:
    """Tests for LineItemSerializer."""

    def get_valid_data(self):
        return {
            "description": "UI Design — Homepage",
            "quantity": "2.00",
            "unit_price": "500.00",
            "tax_rate": "7.50",
        }

    def test_valid_data_passes(self):
        serializer = LineItemSerializer(data=self.get_valid_data())
        assert serializer.is_valid(), serializer.errors

    def test_missing_description_fails(self):
        data = self.get_valid_data()
        del data["description"]
        serializer = LineItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_missing_quantity_fails(self):
        data = self.get_valid_data()
        del data["quantity"]
        serializer = LineItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "quantity" in serializer.errors

    def test_missing_unit_price_fails(self):
        data = self.get_valid_data()
        del data["unit_price"]
        serializer = LineItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "unit_price" in serializer.errors

    def test_zero_quantity_fails(self):
        data = self.get_valid_data()
        data["quantity"] = "0"
        serializer = LineItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "quantity" in serializer.errors

    def test_negative_unit_price_fails(self):
        data = self.get_valid_data()
        data["unit_price"] = "-100"
        serializer = LineItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "unit_price" in serializer.errors

    def test_tax_rate_defaults_to_zero(self):
        data = self.get_valid_data()
        del data["tax_rate"]
        serializer = LineItemSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["tax_rate"] == Decimal("0.00")

    def test_tax_rate_above_100_fails(self):
        data = self.get_valid_data()
        data["tax_rate"] = "101"
        serializer = LineItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "tax_rate" in serializer.errors


@pytest.mark.django_db
class TestInvoiceSerializer:
    """Tests for InvoiceSerializer."""

    def get_valid_data(self, client_id):
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
                {
                    "description": "Frontend Development",
                    "quantity": "2.00",
                    "unit_price": "500.00",
                    "tax_rate": "0.00",
                },
            ],
        }

    def test_valid_invoice_data_passes(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        serializer = InvoiceSerializer(
            data=self.get_valid_data(client.id),
            context={"request": type("Request", (), {"user": user})()}
        )
        assert serializer.is_valid(), serializer.errors

    def test_missing_client_fails(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        data = self.get_valid_data(client.id)
        del data["client"]
        serializer = InvoiceSerializer(data=data)
        assert not serializer.is_valid()
        assert "client" in serializer.errors

    def test_empty_line_items_fails(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        data = self.get_valid_data(client.id)
        data["line_items"] = []
        serializer = InvoiceSerializer(data=data)
        assert not serializer.is_valid()
        assert "line_items" in serializer.errors

    def test_due_date_before_issue_date_fails(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        data = self.get_valid_data(client.id)
        data["due_date"] = str(date.today() - timedelta(days=1))
        serializer = InvoiceSerializer(data=data)
        assert not serializer.is_valid()
        assert "due_date" in serializer.errors

    def test_invalid_currency_fails(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        data = self.get_valid_data(client.id)
        data["currency"] = "INVALID"
        serializer = InvoiceSerializer(data=data)
        assert not serializer.is_valid()
        assert "currency" in serializer.errors

    def test_negative_discount_fails(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        data = self.get_valid_data(client.id)
        data["discount_amount"] = "-100"
        serializer = InvoiceSerializer(data=data)
        assert not serializer.is_valid()
        assert "discount_amount" in serializer.errors