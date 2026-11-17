import pytest
from django.core import mail
from tests.factories import UserFactory, ClientFactory, InvoiceFactory, LineItemFactory
from apps.notifications.tasks import (
    send_verification_email_task,
    send_password_reset_email_task,
    send_invoice_email_task,
    send_payment_receipt_task,
)


@pytest.mark.django_db
class TestNotificationTasks:
    """Tests for email notification tasks with HTML template rendering."""

    def test_send_verification_email_task(self):
        user = UserFactory(email="sarah@example.com", full_name="Sarah Connor")
        result = send_verification_email_task.apply(
            args=[str(user.id), user.email, user.full_name, "849201"]
        ).get()

        assert result is True
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert "Your FlowBill Verification Code: 849201" in email.subject
        assert email.to == ["sarah@example.com"]
        assert "849201" in email.body
        # Check HTML alternative attached
        assert len(email.alternatives) == 1
        html_body, mime_type = email.alternatives[0]
        assert mime_type == "text/html"
        assert "849201" in html_body
        assert "Sarah Connor" in html_body
        assert "Verification Code" in html_body

    def test_verification_email_respects_frontend_url_setting(self):
        from django.test import override_settings

        user = UserFactory(email="prod@example.com", full_name="Prod User")
        with override_settings(FRONTEND_URL="https://app.flowbill.io/"):
            send_verification_email_task.apply(
                args=[str(user.id), user.email, user.full_name, "654321"]
            ).get()

        html_body, _ = mail.outbox[-1].alternatives[0]
        assert "https://app.flowbill.io/verify-email?email=prod@example.com&amp;otp=654321" in html_body

    def test_send_password_reset_email_task(self):
        user = UserFactory(email="john@example.com", full_name="John Wick")
        result = send_password_reset_email_task.apply(
            args=[str(user.id), user.email, user.full_name, "123987"]
        ).get()

        assert result is True
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert "123987" in email.subject
        assert email.to == ["john@example.com"]
        assert len(email.alternatives) == 1
        html_body, mime_type = email.alternatives[0]
        assert mime_type == "text/html"
        assert "123987" in html_body
        assert "Password Reset Request" in html_body

    def test_send_invoice_email_task_with_pdf(self):
        user = UserFactory(email="agency@example.com", full_name="Agency Owner")
        client = ClientFactory(owner=user, email="client@corp.com", name="Client Acme")
        invoice = InvoiceFactory(owner=user, client=client)
        from decimal import Decimal
        LineItemFactory(invoice=invoice, description="Web Development", quantity=Decimal("10.00"), unit_price=Decimal("100.00"))

        result = send_invoice_email_task.apply(
            args=[str(invoice.id), client.email, client.name, "http://localhost:3000/portal/test-token"]
        ).get()

        assert result is True
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert invoice.number in email.subject
        assert email.to == ["client@corp.com"]
        assert len(email.alternatives) == 1
        html_body, _ = email.alternatives[0]
        assert invoice.number in html_body
        assert "http://localhost:3000/portal/test-token" in html_body
        # Verify PDF attachment
        assert len(email.attachments) == 1
        filename, content, content_type = email.attachments[0]
        assert filename == f"{invoice.number}.pdf"
        assert content_type == "application/pdf"
        assert len(content) > 0

    def test_send_payment_receipt_task(self):
        user = UserFactory(email="freelancer@example.com", full_name="Freelancer Dev")
        client = ClientFactory(owner=user, email="client@corp.com")
        invoice = InvoiceFactory(owner=user, client=client)

        result = send_payment_receipt_task.apply(
            args=[
                str(invoice.id),
                client.email,
                "1000.00",
                "USD",
                "PAY-REF-123456",
                "Paystack Card",
            ]
        ).get()

        assert result is True
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert f"Payment Receipt for Invoice {invoice.number}" in email.subject
        assert email.to == ["client@corp.com"]
        assert len(email.alternatives) == 1
        html_body, _ = email.alternatives[0]
        assert "PAY-REF-123456" in html_body
        assert "1000.00" in html_body
        assert "Payment Received!" in html_body
