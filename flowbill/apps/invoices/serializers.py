import structlog
from decimal import Decimal
from rest_framework import serializers
from .models import Invoice, LineItem, InvoiceEvent, CURRENCY_CHOICES

logger = structlog.get_logger(__name__)

VALID_CURRENCIES = [code for code, _ in CURRENCY_CHOICES]


class LineItemSerializer(serializers.ModelSerializer):
    """Serializer for invoice line items."""

    class Meta:
        model = LineItem
        fields = ("id", "description", "quantity", "unit_price", "tax_rate", "total")
        read_only_fields = ("id", "total")

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative.")
        return value

    def validate_tax_rate(self, value):
        if value is None:
            return Decimal("0.00")
        if value < 0 or value > 100:
            raise serializers.ValidationError("Tax rate must be between 0 and 100.")
        return value

    def get_fields(self):
        fields = super().get_fields()
        fields["tax_rate"].required = False
        fields["tax_rate"].default = Decimal("0.00")
        return fields


class InvoiceEventSerializer(serializers.ModelSerializer):
    """Read-only serializer for invoice audit events."""

    class Meta:
        model = InvoiceEvent
        fields = ("id", "event_type", "description", "metadata", "created_at")
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    """
    Full invoice serializer — handles create and retrieve.
    Line items are nested and created atomically with the invoice.
    """

    line_items = LineItemSerializer(many=True)
    events = InvoiceEventSerializer(many=True, read_only=True)
    client = serializers.UUIDField()

    class Meta:
        model = Invoice
        fields = (
            "id",
            "client",
            "number",
            "status",
            "issue_date",
            "due_date",
            "currency",
            "exchange_rate",
            "subtotal",
            "tax_amount",
            "discount_amount",
            "total",
            "notes",
            "payment_terms",
            "line_items",
            "events",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "number",
            "status",
            "subtotal",
            "tax_amount",
            "total",
            "events",
            "created_at",
            "updated_at",
        )

    def validate_currency(self, value):
        if value not in VALID_CURRENCIES:
            raise serializers.ValidationError(
                f"Invalid currency. Choose from: {', '.join(VALID_CURRENCIES)}"
            )
        return value

    def validate_discount_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Discount amount cannot be negative.")
        return value

    def validate_line_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one line item is required.")
        return value

    def validate(self, attrs):
        issue_date = attrs.get("issue_date")
        due_date = attrs.get("due_date")
        if issue_date and due_date and due_date < issue_date:
            raise serializers.ValidationError({
                "due_date": "Due date must be on or after the issue date."
            })
        return attrs


class InvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    client_name = serializers.CharField(source="client.name", read_only=True)
    client_company = serializers.CharField(source="client.company_name", read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "number",
            "status",
            "client_name",
            "client_company",
            "total",
            "currency",
            "issue_date",
            "due_date",
        )
        read_only_fields = fields


class MarkPaidSerializer(serializers.Serializer):
    """Validates input for manually marking an invoice as paid."""

    paid_at = serializers.DateField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value