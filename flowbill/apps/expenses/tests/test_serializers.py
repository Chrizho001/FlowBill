import pytest
from decimal import Decimal
from datetime import date
from tests.factories import UserFactory, ClientFactory
from apps.expenses.serializers import ExpenseSerializer


@pytest.mark.django_db
class TestExpenseSerializer:
    """Tests for ExpenseSerializer."""

    def get_valid_data(self):
        return {
            "amount": "15000.00",
            "currency": "NGN",
            "category": "software",
            "description": "Figma annual subscription",
            "date": str(date.today()),
            "notes": "Design tool",
        }

    def test_valid_data_passes(self):
        serializer = ExpenseSerializer(data=self.get_valid_data())
        assert serializer.is_valid(), serializer.errors

    def test_missing_amount_fails(self):
        data = self.get_valid_data()
        del data["amount"]
        serializer = ExpenseSerializer(data=data)
        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_missing_category_fails(self):
        data = self.get_valid_data()
        del data["category"]
        serializer = ExpenseSerializer(data=data)
        assert not serializer.is_valid()
        assert "category" in serializer.errors

    def test_missing_description_fails(self):
        data = self.get_valid_data()
        del data["description"]
        serializer = ExpenseSerializer(data=data)
        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_missing_date_fails(self):
        data = self.get_valid_data()
        del data["date"]
        serializer = ExpenseSerializer(data=data)
        assert not serializer.is_valid()
        assert "date" in serializer.errors

    def test_zero_amount_fails(self):
        data = self.get_valid_data()
        data["amount"] = "0.00"
        serializer = ExpenseSerializer(data=data)
        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_negative_amount_fails(self):
        data = self.get_valid_data()
        data["amount"] = "-100.00"
        serializer = ExpenseSerializer(data=data)
        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_invalid_category_fails(self):
        data = self.get_valid_data()
        data["category"] = "invalid_category"
        serializer = ExpenseSerializer(data=data)
        assert not serializer.is_valid()
        assert "category" in serializer.errors

    def test_invalid_currency_fails(self):
        data = self.get_valid_data()
        data["currency"] = "INVALID"
        serializer = ExpenseSerializer(data=data)
        assert not serializer.is_valid()
        assert "currency" in serializer.errors

    def test_future_date_fails(self):
        from datetime import timedelta
        data = self.get_valid_data()
        data["date"] = str(date.today() + timedelta(days=1))
        serializer = ExpenseSerializer(data=data)
        assert not serializer.is_valid()
        assert "date" in serializer.errors

    def test_notes_are_optional(self):
        data = self.get_valid_data()
        del data["notes"]
        serializer = ExpenseSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_client_is_optional(self):
        data = self.get_valid_data()
        serializer = ExpenseSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_owner_not_in_input(self):
        data = self.get_valid_data()
        data["owner"] = "some-uuid"
        serializer = ExpenseSerializer(data=data)
        assert serializer.is_valid()
        assert "owner" not in serializer.validated_data

    def test_output_includes_id(self):
        user = UserFactory()
        from tests.factories import ExpenseFactory
        expense = ExpenseFactory(owner=user)
        serializer = ExpenseSerializer(expense)
        assert "id" in serializer.data

    def test_output_excludes_is_deleted(self):
        user = UserFactory()
        from tests.factories import ExpenseFactory
        expense = ExpenseFactory(owner=user)
        serializer = ExpenseSerializer(expense)
        assert "is_deleted" not in serializer.data