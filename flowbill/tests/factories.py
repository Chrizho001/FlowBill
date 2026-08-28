import factory
from factory.django import DjangoModelFactory
from faker import Faker
from decimal import Decimal
from datetime import date, timedelta

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = "accounts.User"
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    full_name = factory.LazyAttribute(lambda _: fake.name())
    password = factory.PostGenerationMethodCall("set_password", "SecurePass123!")
    is_verified = True
    is_active = True

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        if create and results:
            instance.save()


class UnverifiedUserFactory(UserFactory):
    is_verified = False


class BusinessProfileFactory(DjangoModelFactory):
    """Factory for creating test business profiles."""

    class Meta:
        model = "accounts.BusinessProfile"

    user = factory.SubFactory(UserFactory)
    business_name = factory.LazyAttribute(lambda _: fake.company())
    logo_url = factory.LazyAttribute(lambda _: fake.image_url())
    phone = factory.LazyAttribute(lambda _: fake.phone_number()[:20])
    website = factory.LazyAttribute(lambda _: fake.url())
    address = factory.LazyAttribute(lambda _: fake.street_address())
    city = factory.LazyAttribute(lambda _: fake.city())
    state = factory.LazyAttribute(lambda _: fake.state())
    country = "US"
    tax_id = factory.LazyAttribute(lambda _: f"TAX-{fake.random_number(digits=8)}")
    bank_name = "First Bank"
    bank_account_name = factory.LazyAttribute(lambda _: fake.name())
    bank_account_number = factory.LazyAttribute(lambda _: str(fake.random_number(digits=10)))
    default_currency = "USD"
    default_payment_terms = "net_30"
    payment_instructions = "Please pay within 30 days via bank transfer."


class ClientFactory(DjangoModelFactory):
    """Factory for creating test clients."""

    class Meta:
        model = "clients.Client"

    owner = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda _: fake.name())
    email = factory.LazyAttribute(lambda _: fake.unique.email())
    phone = factory.LazyAttribute(lambda _: fake.phone_number()[:20])
    company_name = factory.LazyAttribute(lambda _: fake.company())
    website = factory.LazyAttribute(lambda _: fake.url())
    address = factory.LazyAttribute(lambda _: fake.street_address())
    city = factory.LazyAttribute(lambda _: fake.city())
    state = factory.LazyAttribute(lambda _: fake.state())
    country = "NG"
    currency = "USD"
    status = "active"
    notes = ""


class InvoiceFactory(DjangoModelFactory):
    """Factory for creating test invoices."""

    class Meta:
        model = "invoices.Invoice"

    owner = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory)
    status = "draft"
    issue_date = factory.LazyAttribute(lambda _: date.today())
    due_date = factory.LazyAttribute(lambda _: date.today() + timedelta(days=30))
    currency = "USD"
    exchange_rate = Decimal("1.00")
    subtotal = Decimal("1000.00")
    tax_amount = Decimal("0.00")
    discount_amount = Decimal("0.00")
    total = Decimal("1000.00")
    notes = "Payment due within 30 days."
    payment_terms = "net_30"


class LineItemFactory(DjangoModelFactory):
    """Factory for creating test line items."""

    class Meta:
        model = "invoices.LineItem"

    invoice = factory.SubFactory(InvoiceFactory)
    description = factory.LazyAttribute(lambda _: fake.bs())
    quantity = Decimal("1.00")
    unit_price = Decimal("500.00")
    tax_rate = Decimal("0.00")
    total = Decimal("500.00")


class ExpenseFactory(DjangoModelFactory):
    """Factory for creating test expenses."""

    class Meta:
        model = "expenses.Expense"

    owner = factory.SubFactory(UserFactory)
    client = None
    amount = Decimal("15000.00")
    currency = "USD"
    category = "software"
    description = factory.LazyAttribute(lambda _: fake.bs())
    date = factory.LazyAttribute(lambda _: date.today())
    receipt_url = ""
    notes = ""