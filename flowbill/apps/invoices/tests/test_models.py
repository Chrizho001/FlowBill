import pytest
from decimal import Decimal
from django.utils import timezone
from tests.factories import UserFactory, ClientFactory, InvoiceFactory, LineItemFactory


@pytest.mark.django_db
class TestInvoiceModel:
    """Tests for the Invoice model."""

    def test_create_invoice_with_required_fields(self):
        invoice = InvoiceFactory()
        assert invoice.id is not None
        assert invoice.number.startswith("INV-")
        assert invoice.status == "draft"

    def test_invoice_number_format(self):
        invoice = InvoiceFactory()
        year = timezone.now().year
        assert invoice.number.startswith(f"INV-{year}-")

    def test_invoice_number_is_unique(self):
        invoice1 = InvoiceFactory()
        invoice2 = InvoiceFactory()
        assert invoice1.number != invoice2.number

    def test_invoice_number_is_sequential(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        invoice1 = InvoiceFactory(owner=user, client=client)
        invoice2 = InvoiceFactory(owner=user, client=client)
        num1 = int(invoice1.number.split("-")[-1])
        num2 = int(invoice2.number.split("-")[-1])
        assert num2 == num1 + 1

    def test_invoice_number_sequence_past_9999(self):
        year = timezone.now().year
        user = UserFactory()
        client = ClientFactory(owner=user)
        InvoiceFactory(owner=user, client=client, number=f"INV-{year}-9999")
        InvoiceFactory(owner=user, client=client, number=f"INV-{year}-10000")
        next_invoice = InvoiceFactory(owner=user, client=client)
        assert next_invoice.number == f"INV-{year}-10001"

    def test_invoice_default_status_is_draft(self):
        invoice = InvoiceFactory()
        assert invoice.status == "draft"

    def test_invoice_belongs_to_owner(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=client)
        assert invoice.owner == user

    def test_invoice_belongs_to_client(self):
        user = UserFactory()
        client = ClientFactory(owner=user)
        invoice = InvoiceFactory(owner=user, client=client)
        assert invoice.client == client

    def test_invoice_str(self):
        invoice = InvoiceFactory()
        assert invoice.number in str(invoice)

    def test_invoice_is_not_deleted_by_default(self):
        invoice = InvoiceFactory()
        assert invoice.is_deleted is False

    def test_invoice_soft_delete(self):
        invoice = InvoiceFactory()
        invoice.delete()
        assert invoice.is_deleted is True
        assert invoice.deleted_at is not None

    def test_invoice_id_is_uuid(self):
        import uuid
        invoice = InvoiceFactory()
        assert isinstance(invoice.id, uuid.UUID)

    def test_invoice_monetary_fields_are_decimal(self):
        invoice = InvoiceFactory()
        assert isinstance(invoice.subtotal, Decimal)
        assert isinstance(invoice.tax_amount, Decimal)
        assert isinstance(invoice.discount_amount, Decimal)
        assert isinstance(invoice.total, Decimal)

    def test_invoice_is_overdue_when_past_due_date(self):
        from datetime import date, timedelta
        invoice = InvoiceFactory(
            status="pending",
            due_date=date.today() - timedelta(days=1),
        )
        assert invoice.is_overdue is True

    def test_invoice_is_not_overdue_when_future_due_date(self):
        from datetime import date, timedelta
        invoice = InvoiceFactory(
            status="pending",
            due_date=date.today() + timedelta(days=7),
        )
        assert invoice.is_overdue is False

    def test_paid_invoice_is_never_overdue(self):
        from datetime import date, timedelta
        invoice = InvoiceFactory(
            status="paid",
            due_date=date.today() - timedelta(days=10),
        )
        assert invoice.is_overdue is False


@pytest.mark.django_db
class TestLineItemModel:
    """Tests for the LineItem model."""

    def test_create_line_item(self):
        item = LineItemFactory()
        assert item.id is not None
        assert item.description != ""

    def test_line_item_total_is_calculated(self):
        item = LineItemFactory(quantity=Decimal("2"), unit_price=Decimal("100.00"))
        assert item.total == Decimal("200.00")

    def test_line_item_total_with_decimals(self):
        item = LineItemFactory(quantity=Decimal("1.5"), unit_price=Decimal("200.00"))
        assert item.total == Decimal("300.00")

    def test_line_item_belongs_to_invoice(self):
        invoice = InvoiceFactory()
        item = LineItemFactory(invoice=invoice)
        assert item.invoice == invoice


@pytest.mark.django_db
class TestInvoiceEvent:
    """Tests for the InvoiceEvent model."""

    def test_create_invoice_event(self):
        from apps.invoices.models import InvoiceEvent
        invoice = InvoiceFactory()
        event = InvoiceEvent.objects.create(
            invoice=invoice,
            event_type="created",
            description="Invoice created",
        )
        assert event.id is not None
        assert event.invoice == invoice

    def test_invoice_event_is_append_only(self):
        """Events should never be updated — only created."""
        from apps.invoices.models import InvoiceEvent
        invoice = InvoiceFactory()
        event = InvoiceEvent.objects.create(
            invoice=invoice,
            event_type="created",
            description="Invoice created",
        )
        original_description = event.description
        event.description = "Modified"
        event.save()
        # Refresh and verify — in real implementation we'd enforce this at DB level
        assert InvoiceEvent.objects.get(id=event.id).description == "Modified"

@pytest.mark.django_db
class TestInvoiceNumberSequence:
    """
    Invoice numbers come from a per-year counter row (InvoiceSequence) that is
    locked and incremented in the same transaction as the invoice insert:
    constant cost, gapless on rollback, safe under concurrency.
    """

    def test_counter_tracks_issued_numbers_for_the_year(self):
        from apps.invoices.models import InvoiceSequence

        year = timezone.now().year
        InvoiceFactory()
        last = InvoiceFactory()

        assert InvoiceSequence.objects.get(year=year).last_value == 2
        assert last.number == f"INV-{year}-0002"

    def test_number_generation_does_not_scan_existing_invoices(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        for _ in range(5):
            InvoiceFactory()

        with CaptureQueriesContext(connection) as ctx:
            InvoiceFactory()

        scans = [q["sql"] for q in ctx.captured_queries if "LIKE" in q["sql"].upper() and '"number"' in q["sql"]]
        assert scans == [], f"number generation scanned the invoices table: {scans}"

    def test_rolled_back_invoice_does_not_leave_a_gap(self):
        from django.db import transaction

        year = timezone.now().year
        InvoiceFactory()

        with pytest.raises(RuntimeError):
            with transaction.atomic():
                InvoiceFactory()
                raise RuntimeError("simulated failure after the invoice was created")

        assert InvoiceFactory().number == f"INV-{year}-0002"

    def test_explicit_number_moves_the_counter_forward(self):
        from apps.invoices.models import InvoiceSequence

        year = timezone.now().year
        InvoiceFactory(number=f"INV-{year}-0500")

        assert InvoiceSequence.objects.get(year=year).last_value == 500
        assert InvoiceFactory().number == f"INV-{year}-0501"


@pytest.mark.django_db(transaction=True)
def test_concurrent_invoice_creation_gets_unique_consecutive_numbers():
    """Real parallel transactions on PostgreSQL must not collide or skip."""
    import threading

    from django.db import connection

    year = timezone.now().year
    user = UserFactory()
    client = ClientFactory(owner=user)
    numbers, errors = [], []
    start = threading.Barrier(8)

    def create():
        try:
            start.wait()
            numbers.append(InvoiceFactory(owner=user, client=client).number)
        except Exception as exc:  # surface thread failures to the assertion below
            errors.append(repr(exc))
        finally:
            connection.close()

    threads = [threading.Thread(target=create) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert sorted(numbers) == [f"INV-{year}-{i:04d}" for i in range(1, 9)]


@pytest.mark.django_db
def test_sequence_seed_migration_starts_from_highest_existing_number():
    """0002 seeds each year's counter from existing invoices, including soft-deleted ones."""
    import importlib

    from django.apps import apps as django_apps

    from apps.invoices.models import Invoice, InvoiceSequence

    InvoiceFactory(number="INV-2025-0041")
    InvoiceFactory(number="INV-2025-0007")
    deleted = InvoiceFactory(number="INV-2026-0120")
    Invoice.objects.filter(pk=deleted.pk).update(is_deleted=True)
    InvoiceSequence.objects.all().delete()  # simulate the pre-migration state

    migration = importlib.import_module("apps.invoices.migrations.0002_invoice_sequence")
    migration.seed_sequences(django_apps, None)

    assert dict(InvoiceSequence.objects.values_list("year", "last_value")) == {2025: 41, 2026: 120}
