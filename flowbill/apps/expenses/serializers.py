from datetime import date
from decimal import Decimal
from rest_framework import serializers
from .models import Expense, CATEGORY_CHOICES, CURRENCY_CHOICES

VALID_CATEGORIES = [c[0] for c in CATEGORY_CHOICES]
VALID_CURRENCIES = [c[0] for c in CURRENCY_CHOICES]


class ExpenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Expense
        fields = (
            "id",
            "client",
            "amount",
            "currency",
            "category",
            "description",
            "date",
            "receipt_url",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "client": {"required": False, "allow_null": True},
            "receipt_url": {"required": False},
            "notes": {"required": False},
        }

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_category(self, value):
        if value not in VALID_CATEGORIES:
            raise serializers.ValidationError(
                f"Invalid category. Choose from: {', '.join(VALID_CATEGORIES)}"
            )
        return value

    def validate_currency(self, value):
        if value not in VALID_CURRENCIES:
            raise serializers.ValidationError(
                f"Invalid currency. Choose from: {', '.join(VALID_CURRENCIES)}"
            )
        return value

    def validate_date(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                "Expense date cannot be in the future."
            )
        return value


class ExpenseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    client_name = serializers.CharField(
        source="client.name", read_only=True, default=None
    )

    class Meta:
        model = Expense
        fields = (
            "id",
            "amount",
            "currency",
            "category",
            "description",
            "date",
            "client_name",
        )
        read_only_fields = fields