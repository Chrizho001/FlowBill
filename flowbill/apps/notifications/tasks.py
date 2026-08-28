import structlog
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email_task(self, user_id: str, email: str, full_name: str, otp: str):
    """
    Asynchronously sends a beautifully styled 6-digit TOTP verification email to the user.
    """
    verification_url = f"http://localhost:3000/verify-email?email={email}&otp={otp}"

    context = {
        "full_name": full_name,
        "otp": otp,
        "verification_url": verification_url,
    }

    # Render HTML template and generate plain text fallback
    html_content = render_to_string("emails/verification_otp.html", context)
    text_content = strip_tags(html_content)

    subject = f"Your FlowBill Verification Code: {otp}"

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("notifications.verification_email_sent", email=email, user_id=user_id)
        return True
    except Exception as exc:
        logger.error(
            "notifications.verification_email_failed",
            email=email,
            user_id=user_id,
            error=str(exc),
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email_task(self, user_id: str, email: str, full_name: str, otp: str):
    """
    Asynchronously sends a beautifully styled 6-digit password reset code to the user.
    """
    reset_url = f"http://localhost:3000/reset-password?email={email}&otp={otp}"

    context = {
        "full_name": full_name,
        "otp": otp,
        "reset_url": reset_url,
    }

    html_content = render_to_string("emails/password_reset_otp.html", context)
    text_content = strip_tags(html_content)

    subject = f"Your FlowBill Password Reset Code: {otp}"

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("notifications.password_reset_email_sent", email=email, user_id=user_id)
        return True
    except Exception as exc:
        logger.error(
            "notifications.password_reset_email_failed",
            email=email,
            user_id=user_id,
            error=str(exc),
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_invoice_email_task(self, invoice_id: str, client_email: str, client_name: str, magic_link: str = ""):
    """
    Asynchronously sends an invoice notification HTML email with WeasyPrint PDF attached.
    """
    from apps.invoices.models import Invoice
    from apps.invoices.pdf import PDFService

    try:
        invoice = Invoice.objects.select_related("owner", "client").get(id=invoice_id)
    except Invoice.DoesNotExist:
        logger.error("notifications.invoice_not_found", invoice_id=invoice_id)
        return False

    issuer_profile = getattr(invoice.owner, "profile", None)
    issuer_name = (
        issuer_profile.business_name
        if issuer_profile and issuer_profile.business_name
        else invoice.owner.full_name
    )

    context = {
        "invoice": invoice,
        "client_name": client_name or invoice.client.name,
        "issuer_name": issuer_name,
        "magic_link": magic_link,
    }

    html_content = render_to_string("emails/invoice_notification.html", context)
    text_content = strip_tags(html_content)
    subject = f"Invoice {invoice.number} from {issuer_name}"

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[client_email],
        )
        msg.attach_alternative(html_content, "text/html")

        # Generate and attach PDF
        try:
            pdf_bytes = PDFService.generate_invoice_pdf(invoice)
            msg.attach(
                f"{invoice.number}.pdf",
                pdf_bytes,
                "application/pdf",
            )
        except Exception as pdf_err:
            logger.warning("notifications.pdf_attachment_failed", invoice_id=invoice_id, error=str(pdf_err))

        msg.send(fail_silently=False)
        logger.info("notifications.invoice_email_sent", invoice_id=invoice_id, email=client_email)
        return True
    except Exception as exc:
        logger.error("notifications.invoice_email_failed", invoice_id=invoice_id, error=str(exc))
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_receipt_task(self, invoice_id: str, recipient_email: str, amount: str, currency: str, reference: str, method: str = "Online", paid_at=None):
    """
    Asynchronously sends a payment confirmation receipt email.
    """
    from apps.invoices.models import Invoice

    try:
        invoice = Invoice.objects.select_related("owner", "client").get(id=invoice_id)
    except Invoice.DoesNotExist:
        logger.error("notifications.payment_invoice_not_found", invoice_id=invoice_id)
        return False

    context = {
        "invoice": invoice,
        "amount": amount,
        "currency": currency,
        "reference": reference,
        "method": method,
        "paid_at": paid_at,
    }

    html_content = render_to_string("emails/payment_receipt.html", context)
    text_content = strip_tags(html_content)
    subject = f"Payment Receipt for Invoice {invoice.number}"

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("notifications.payment_receipt_sent", invoice_id=invoice_id, email=recipient_email)
        return True
    except Exception as exc:
        logger.error("notifications.payment_receipt_failed", invoice_id=invoice_id, error=str(exc))
        raise self.retry(exc=exc)