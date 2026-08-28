import structlog
from django.template.loader import render_to_string
from django.conf import settings

logger = structlog.get_logger(__name__)


class PDFService:
    """
    Generates invoice PDFs using WeasyPrint.
    Renders the HTML template with invoice context,
    then converts to PDF bytes.
    """

    TEMPLATE = "invoices/invoice_pdf.html"

    @staticmethod
    def generate_invoice_pdf(invoice) -> bytes:
        """
        Generates a PDF for the given invoice.
        Returns raw PDF bytes ready to be served or saved.
        Raises RuntimeError if generation fails.
        """
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
        except ImportError:
            raise RuntimeError(
                "WeasyPrint is not installed. Run: uv add weasyprint"
            )

        try:
            # Build template context
            context = PDFService._build_context(invoice)

            # Render HTML string
            html_string = render_to_string(PDFService.TEMPLATE, context)

            # Convert to PDF
            font_config = FontConfiguration()
            html = HTML(string=html_string, base_url=settings.BASE_DIR)
            pdf_bytes = html.write_pdf(font_config=font_config)

            logger.info(
                "pdf.generated",
                invoice_id=str(invoice.id),
                invoice_number=invoice.number,
                size_bytes=len(pdf_bytes),
            )

            return pdf_bytes

        except Exception as e:
            logger.error(
                "pdf.generation_failed",
                invoice_id=str(invoice.id),
                error=str(e),
            )
            raise RuntimeError(f"PDF generation failed: {str(e)}")

    @staticmethod
    def _build_context(invoice) -> dict:
        """Builds the template context for the invoice PDF."""
        line_items = invoice.line_items.all()
        owner_profile = getattr(invoice.owner, "profile", None)
        payment_instructions = (
            owner_profile.payment_instructions
            if owner_profile and owner_profile.payment_instructions
            else ""
        )

        return {
            "invoice": invoice,
            "owner": invoice.owner,
            "owner_profile": owner_profile,
            "client": invoice.client,
            "line_items": line_items,
            "payment_instructions": payment_instructions,
        }