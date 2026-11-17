"""
Invoice PDF rendering: the tenant logo is embedded as a data: URI and WeasyPrint
gets no network or filesystem access (closes the SSRF / DNS-rebinding class).
"""

import base64
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from PIL import Image

from apps.accounts.models import BusinessProfile
from apps.accounts.services import AccountsService
from apps.invoices.models import Invoice
from apps.invoices.pdf import PDFService
from tests.factories import InvoiceFactory


@pytest.fixture(autouse=True)
def media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def png_upload(size=(300, 120)):
    buf = io.BytesIO()
    Image.new("RGB", size, (39, 50, 94)).save(buf, format="PNG")
    return SimpleUploadedFile("logo.png", buf.getvalue(), content_type="image/png")


def invoice_with_logo(business_name="Kemi Okafor Design"):
    invoice = InvoiceFactory()
    profile, _ = BusinessProfile.objects.get_or_create(user=invoice.owner)
    profile.business_name = business_name
    profile.save()
    AccountsService.set_logo(invoice.owner, png_upload())
    # Reload like the real PDF endpoint does (avoids the stale cached owner.profile).
    return Invoice.objects.get(pk=invoice.pk)


class TestPdfUrlFetcher:
    @pytest.mark.parametrize(
        "url",
        [
            "http://169.254.169.254/latest/meta-data/",
            "https://example.com/logo.png",
            "http://localhost:8000/admin",
            "file:///etc/passwd",
            "ftp://example.com/x.png",
        ],
    )
    def test_network_and_file_urls_are_refused(self, url):
        with pytest.raises(ValueError, match="disallowed protocol"):
            PDFService.url_fetcher().fetch(url)

    def test_embedded_data_uri_is_allowed(self):
        payload = base64.b64encode(b"hello").decode()
        response = PDFService.url_fetcher().fetch(f"data:text/plain;base64,{payload}")
        assert response.read() == b"hello"


@pytest.mark.django_db
class TestPdfLogo:
    def test_context_embeds_logo_as_png_data_uri(self):
        context = PDFService._build_context(invoice_with_logo())

        uri = context["logo_data_uri"]
        assert uri.startswith("data:image/png;base64,")
        decoded = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1])))
        assert decoded.format == "PNG"

    def test_context_has_no_logo_when_none_uploaded(self):
        context = PDFService._build_context(InvoiceFactory())
        assert context["logo_data_uri"] is None

    def test_template_shows_tenant_logo_and_business_name(self):
        invoice = invoice_with_logo("Kemi Okafor Design")
        html = render_to_string(PDFService.TEMPLATE, PDFService._build_context(invoice))

        assert '<img class="brand-logo" src="data:image/png;base64,' in html
        assert "Kemi Okafor Design" in html.split('class="header"', 1)[1].split("</div>\n  </div>", 1)[0]

    def test_generated_pdf_with_logo_is_valid(self):
        pdf = PDFService.generate_invoice_pdf(invoice_with_logo())
        assert pdf.startswith(b"%PDF")
