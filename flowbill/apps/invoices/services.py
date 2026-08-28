import structlog
from decimal import Decimal
from django.db import transaction
from django.db.models import QuerySet
from rest_framework import serializers
from .models import Invoice, LineItem, InvoiceEvent

logger = structlog.get_logger(__name__)


class InvoiceService:
    """All business logic for invoice management."""

    @staticmethod
    def get_invoices(user, status: str = None, client_id: str = None) -> QuerySet:
        queryset = Invoice.objects.filter(
            owner=user,
            is_deleted=False,
        ).select_related("client")

        if status:
            queryset = queryset.filter(status=status)

        if client_id:
            queryset = queryset.filter(client_id=client_id)

        return queryset.order_by("-created_at")

    @staticmethod
    def get_invoice(user, invoice_id: str) -> Invoice:
        return Invoice.objects.select_related("client").prefetch_related(
            "line_items", "events"
        ).get(
            id=invoice_id,
            owner=user,
            is_deleted=False,
        )

    @staticmethod
    @transaction.atomic
    def create_invoice(user, validated_data: dict) -> Invoice:
        """
        Creates an invoice with line items in a single atomic transaction.
        Calculates all totals server-side.
        """
        from apps.clients.models import Client

        # Validate client belongs to this user
        client_id = validated_data.pop("client")
        try:
            client = Client.objects.get(id=client_id, owner=user, is_deleted=False)
        except Client.DoesNotExist:
            raise serializers.ValidationError({
                "client": "Client not found or does not belong to you."
            })

        line_items_data = validated_data.pop("line_items")

        # Calculate totals
        subtotal, tax_amount = InvoiceService._calculate_totals(line_items_data)
        discount = validated_data.get("discount_amount", Decimal("0.00"))
        total = subtotal + tax_amount - discount

        invoice = Invoice.objects.create(
            owner=user,
            client=client,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=total,
            **validated_data,
        )

        # Create line items
        LineItem.objects.bulk_create([
            LineItem(
                invoice=invoice,
                description=item["description"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                tax_rate=item.get("tax_rate", Decimal("0.00")),
                total=item["quantity"] * item["unit_price"],
            )
            for item in line_items_data
        ])

        # Log creation event
        InvoiceService._log_event(
            invoice=invoice,
            event_type="created",
            description=f"Invoice {invoice.number} created.",
        )

        logger.info(
            "invoices.created",
            invoice_id=str(invoice.id),
            number=invoice.number,
            owner_id=str(user.id),
            total=str(total),
        )

        return invoice

    @staticmethod
    @transaction.atomic
    def update_invoice(invoice: Invoice, validated_data: dict) -> Invoice:
        """Updates a draft invoice. Raises error if not in draft status."""
        if invoice.status != "draft":
            raise serializers.ValidationError(
                "Only draft invoices can be edited."
            )

        line_items_data = validated_data.pop("line_items", None)

        for field, value in validated_data.items():
            setattr(invoice, field, value)

        if line_items_data is not None:
            # Recalculate totals with new line items
            subtotal, tax_amount = InvoiceService._calculate_totals(line_items_data)
            discount = invoice.discount_amount
            invoice.subtotal = subtotal
            invoice.tax_amount = tax_amount
            invoice.total = subtotal + tax_amount - discount

            # Replace line items
            invoice.line_items.all().delete()
            LineItem.objects.bulk_create([
                LineItem(
                    invoice=invoice,
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    tax_rate=item.get("tax_rate", Decimal("0.00")),
                    total=item["quantity"] * item["unit_price"],
                )
                for item in line_items_data
            ])

        invoice.save()
        logger.info("invoices.updated", invoice_id=str(invoice.id))
        return invoice

    @staticmethod
    def cancel_invoice(invoice: Invoice) -> Invoice:
        """Cancels a draft or pending invoice."""
        if invoice.status not in ("draft", "pending"):
            raise serializers.ValidationError(
                "Only draft or pending invoices can be cancelled."
            )
        invoice.status = "cancelled"
        invoice.save(update_fields=["status", "updated_at"])

        InvoiceService._log_event(
            invoice=invoice,
            event_type="cancelled",
            description=f"Invoice {invoice.number} was cancelled.",
        )
        logger.info("invoices.cancelled", invoice_id=str(invoice.id))
        return invoice

    @staticmethod
    def send_invoice(invoice: Invoice) -> Invoice:
        """Sends invoice email and transitions status to pending."""
        if invoice.status != "draft":
            raise serializers.ValidationError(
                "Only draft invoices can be sent."
            )

        invoice.status = "pending"
        invoice.save(update_fields=["status", "updated_at"])

        InvoiceService._log_event(
            invoice=invoice,
            event_type="sent",
            description=f"Invoice {invoice.number} sent to {invoice.client.email}.",
        )

        # Send email async — will use Celery when wired up
        try:
            from apps.notifications.tasks import send_invoice_email_task
            send_invoice_email_task.delay(
                invoice_id=str(invoice.id),
                client_email=invoice.client.email,
                client_name=invoice.client.name,
            )
        except Exception as e:
            logger.error("invoices.send_email_failed", invoice_id=str(invoice.id), error=str(e))

        logger.info("invoices.sent", invoice_id=str(invoice.id))
        return invoice

    @staticmethod
    def mark_paid(invoice: Invoice, paid_at, amount: Decimal, notes: str = "") -> Invoice:
        """Manually marks an invoice as paid."""
        if invoice.status not in ("pending", "overdue"):
            raise serializers.ValidationError(
                "Only pending or overdue invoices can be marked as paid."
            )

        invoice.status = "paid"
        invoice.save(update_fields=["status", "updated_at"])

        InvoiceService._log_event(
            invoice=invoice,
            event_type="paid",
            description=f"Invoice {invoice.number} marked as paid. Amount: {amount}.",
            metadata={"amount": str(amount), "paid_at": str(paid_at), "notes": notes},
        )

        logger.info("invoices.marked_paid", invoice_id=str(invoice.id), amount=str(amount))
        return invoice

    @staticmethod
    @transaction.atomic
    def duplicate_invoice(invoice: Invoice) -> Invoice:
        """Creates a new draft invoice copying all data from the original."""
        from datetime import date, timedelta

        line_items = list(invoice.line_items.all())

        new_invoice = Invoice.objects.create(
            owner=invoice.owner,
            client=invoice.client,
            status="draft",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            currency=invoice.currency,
            exchange_rate=invoice.exchange_rate,
            subtotal=invoice.subtotal,
            tax_amount=invoice.tax_amount,
            discount_amount=invoice.discount_amount,
            total=invoice.total,
            notes=invoice.notes,
            payment_terms=invoice.payment_terms,
        )

        LineItem.objects.bulk_create([
            LineItem(
                invoice=new_invoice,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                tax_rate=item.tax_rate,
                total=item.total,
            )
            for item in line_items
        ])

        InvoiceService._log_event(
            invoice=new_invoice,
            event_type="duplicated",
            description=f"Duplicated from invoice {invoice.number}.",
            metadata={"source_invoice_id": str(invoice.id)},
        )

        logger.info(
            "invoices.duplicated",
            source_id=str(invoice.id),
            new_id=str(new_invoice.id),
        )
        return new_invoice

    @staticmethod
    def _calculate_totals(line_items_data: list) -> tuple:
        """Returns (subtotal, tax_amount) from line items data."""
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")

        for item in line_items_data:
            qty = item["quantity"]
            price = item["unit_price"]
            tax_rate = item.get("tax_rate", Decimal("0.00"))
            line_total = (qty * price).quantize(Decimal("0.01"))
            line_tax = (line_total * tax_rate / 100).quantize(Decimal("0.01"))
            subtotal += line_total
            tax_amount += line_tax

        return subtotal, tax_amount

    @staticmethod
    def _log_event(invoice: Invoice, event_type: str, description: str, metadata: dict = None):
        InvoiceEvent.objects.create(
            invoice=invoice,
            event_type=event_type,
            description=description,
            metadata=metadata or {},
        )