import pytest
from decimal import Decimal
from datetime import date
from tests.factories import UserFactory, ClientFactory, ExpenseFactory


@pytest.mark.django_db
class TestExpenseModel:
    """Tests for the Expense model."""

    def test_create_expense_with_required_fields(self):
        expense = ExpenseFactory()
        assert expense.id is not None
        assert expense.amount > 0
        assert expense.description != ""

    def test_expense_belongs_to_owner(self):
        user = UserFactory()
        expense = ExpenseFactory(owner=user)
        assert expense.owner == user

    def test_expense_default_currency_is_usd(self):
        expense = ExpenseFactory()
        assert expense.currency == "USD"

    def test_expense_id_is_uuid(self):
        import uuid
        expense = ExpenseFactory()
        assert isinstance(expense.id, uuid.UUID)

    def test_expense_str(self):
        expense = ExpenseFactory(description="Figma subscription", amount=Decimal("15000.00"))
        assert "Figma subscription" in str(expense)

    def test_expense_date_defaults_to_today(self):
        expense = ExpenseFactory()
        assert expense.date == date.today()

    def test_expense_can_be_linked_to_client(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        expense = ExpenseFactory(owner=user, client=client)
        assert expense.client == client

    def test_expense_client_is_optional(self):
        expense = ExpenseFactory(client=None)
        assert expense.client is None

    def test_expense_receipt_url_is_optional(self):
        expense = ExpenseFactory(receipt_url="")
        assert expense.receipt_url == ""

    def test_expense_soft_delete(self):
        expense = ExpenseFactory()
        expense.delete()
        assert expense.is_deleted is True
        assert expense.deleted_at is not None

    def test_expense_is_not_deleted_by_default(self):
        expense = ExpenseFactory()
        assert expense.is_deleted is False

    def test_expense_valid_categories(self):
        from apps.expenses.models import CATEGORY_CHOICES
        categories = [c[0] for c in CATEGORY_CHOICES]
        assert "software" in categories
        assert "equipment" in categories
        assert "marketing" in categories
        assert "travel" in categories
        assert "education" in categories
        assert "internet" in categories
        assert "other" in categories