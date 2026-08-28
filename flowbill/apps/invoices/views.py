import structlog
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Invoice
from .serializers import (
    InvoiceSerializer,
    InvoiceListSerializer,
    MarkPaidSerializer,
)
from .services import InvoiceService
from core.pagination import StandardPagination

logger = structlog.get_logger(__name__)


class InvoiceListCreateView(APIView):
    """
    GET  /api/v1/invoices/  — list all invoices
    POST /api/v1/invoices/  — create invoice with line items
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get("status")
        client_id = request.query_params.get("client")

        invoices = InvoiceService.get_invoices(
            user=request.user,
            status=status_filter,
            client_id=client_id,
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(invoices, request)
        serializer = InvoiceListSerializer(page, many=True)

        logger.info(
            "invoices.list.success",
            user_id=str(request.user.id),
            count=len(page),
            status_filter=status_filter,
            client_id=client_id,
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = InvoiceSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        invoice = InvoiceService.create_invoice(
            user=request.user,
            validated_data=serializer.validated_data,
        )

        logger.info(
            "invoices.create.success",
            user_id=str(request.user.id),
            invoice_id=str(invoice.id),
            number=invoice.number,
            total=str(invoice.total),
        )

        return Response({
            "status": "success",
            "message": "Invoice created successfully.",
            "data": InvoiceSerializer(invoice).data,
        }, status=status.HTTP_201_CREATED)


class InvoiceRetrieveUpdateDeleteView(APIView):
    """
    GET    /api/v1/invoices/{id}/  — retrieve invoice with line items and events
    PATCH  /api/v1/invoices/{id}/  — update draft invoice
    DELETE /api/v1/invoices/{id}/  — cancel invoice
    """
    permission_classes = [IsAuthenticated]

    def get_invoice(self, request, invoice_id):
        try:
            return InvoiceService.get_invoice(request.user, invoice_id)
        except Invoice.DoesNotExist:
            logger.warning(
                "invoices.not_found",
                user_id=str(request.user.id),
                invoice_id=str(invoice_id),
            )
            return None

    def get(self, request, invoice_id):
        invoice = self.get_invoice(request, invoice_id)
        if not invoice:
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Invoice not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        logger.info(
            "invoices.retrieve.success",
            user_id=str(request.user.id),
            invoice_id=str(invoice.id),
            number=invoice.number,
        )

        return Response({
            "status": "success",
            "data": InvoiceSerializer(invoice).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, invoice_id):
        invoice = self.get_invoice(request, invoice_id)
        if not invoice:
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Invoice not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = InvoiceSerializer(
            invoice,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        updated = InvoiceService.update_invoice(
            invoice=invoice,
            validated_data=serializer.validated_data,
        )

        logger.info(
            "invoices.update.success",
            user_id=str(request.user.id),
            invoice_id=str(updated.id),
            number=updated.number,
        )

        return Response({
            "status": "success",
            "message": "Invoice updated successfully.",
            "data": InvoiceSerializer(updated).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request, invoice_id):
        invoice = self.get_invoice(request, invoice_id)
        if not invoice:
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Invoice not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        InvoiceService.cancel_invoice(invoice)

        logger.info(
            "invoices.cancel.success",
            user_id=str(request.user.id),
            invoice_id=str(invoice.id),
            number=invoice.number,
        )

        return Response({
            "status": "success",
            "message": "Invoice cancelled successfully.",
        }, status=status.HTTP_200_OK)


class InvoiceSendView(APIView):
    """POST /api/v1/invoices/{id}/send/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, invoice_id):
        try:
            invoice = InvoiceService.get_invoice(request.user, invoice_id)
        except Invoice.DoesNotExist:
            logger.warning(
                "invoices.send.not_found",
                user_id=str(request.user.id),
                invoice_id=str(invoice_id),
            )
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Invoice not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        invoice = InvoiceService.send_invoice(invoice)

        logger.info(
            "invoices.send.success",
            user_id=str(request.user.id),
            invoice_id=str(invoice.id),
            number=invoice.number,
            client_email=invoice.client.email,
        )

        return Response({
            "status": "success",
            "message": f"Invoice {invoice.number} sent successfully.",
            "data": InvoiceSerializer(invoice).data,
        }, status=status.HTTP_200_OK)


class InvoiceMarkPaidView(APIView):
    """POST /api/v1/invoices/{id}/mark-paid/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, invoice_id):
        try:
            invoice = InvoiceService.get_invoice(request.user, invoice_id)
        except Invoice.DoesNotExist:
            logger.warning(
                "invoices.mark_paid.not_found",
                user_id=str(request.user.id),
                invoice_id=str(invoice_id),
            )
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Invoice not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = MarkPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice = InvoiceService.mark_paid(
            invoice=invoice,
            paid_at=serializer.validated_data["paid_at"],
            amount=serializer.validated_data["amount"],
            notes=serializer.validated_data.get("notes", ""),
        )

        logger.info(
            "invoices.mark_paid.success",
            user_id=str(request.user.id),
            invoice_id=str(invoice.id),
            number=invoice.number,
            amount=str(serializer.validated_data["amount"]),
        )

        return Response({
            "status": "success",
            "message": f"Invoice {invoice.number} marked as paid.",
            "data": InvoiceSerializer(invoice).data,
        }, status=status.HTTP_200_OK)


class InvoiceDuplicateView(APIView):
    """POST /api/v1/invoices/{id}/duplicate/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, invoice_id):
        try:
            invoice = InvoiceService.get_invoice(request.user, invoice_id)
        except Invoice.DoesNotExist:
            logger.warning(
                "invoices.duplicate.not_found",
                user_id=str(request.user.id),
                invoice_id=str(invoice_id),
            )
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Invoice not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        new_invoice = InvoiceService.duplicate_invoice(invoice)

        logger.info(
            "invoices.duplicate.success",
            user_id=str(request.user.id),
            source_id=str(invoice.id),
            new_id=str(new_invoice.id),
            new_number=new_invoice.number,
        )

        return Response({
            "status": "success",
            "message": "Invoice duplicated successfully.",
            "data": InvoiceSerializer(new_invoice).data,
        }, status=status.HTTP_201_CREATED)


class InvoiceEventsView(APIView):
    """GET /api/v1/invoices/{id}/events/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id):
        try:
            invoice = InvoiceService.get_invoice(request.user, invoice_id)
        except Invoice.DoesNotExist:
            logger.warning(
                "invoices.events.not_found",
                user_id=str(request.user.id),
                invoice_id=str(invoice_id),
            )
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Invoice not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        from .serializers import InvoiceEventSerializer
        events = invoice.events.all().order_by("created_at")
        serializer = InvoiceEventSerializer(events, many=True)

        logger.info(
            "invoices.events.retrieved",
            user_id=str(request.user.id),
            invoice_id=str(invoice.id),
            event_count=events.count(),
        )

        return Response({
            "status": "success",
            "data": serializer.data,
        }, status=status.HTTP_200_OK)
    


class InvoicePDFView(APIView):
    """
    GET /api/v1/invoices/{id}/pdf/
    Generates and returns the invoice as a downloadable PDF.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id):
        from django.http import HttpResponse
        from .pdf import PDFService

        try:
            invoice = InvoiceService.get_invoice(request.user, invoice_id)
        except Invoice.DoesNotExist:
            logger.warning(
                "invoices.pdf.not_found",
                user_id=str(request.user.id),
                invoice_id=str(invoice_id),
            )
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Invoice not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            pdf_bytes = PDFService.generate_invoice_pdf(invoice)
        except RuntimeError as e:
            logger.error(
                "invoices.pdf.generation_failed",
                user_id=str(request.user.id),
                invoice_id=str(invoice.id),
                error=str(e),
            )
            return Response({
                "status": "error",
                "code": "PDF_GENERATION_FAILED",
                "message": str(e),
                "fields": {},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        filename = f"{invoice.number}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(pdf_bytes)

        logger.info(
            "invoices.pdf.downloaded",
            invoice_id=str(invoice.id),
            user_id=str(request.user.id),
            number=invoice.number,
            size_bytes=len(pdf_bytes),
        )

        return response