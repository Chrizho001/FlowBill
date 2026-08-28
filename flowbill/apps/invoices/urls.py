from django.urls import path
from .views import (
    InvoiceListCreateView,
    InvoiceRetrieveUpdateDeleteView,
    InvoiceSendView,
    InvoiceMarkPaidView,
    InvoiceDuplicateView,
    InvoiceEventsView,
    InvoicePDFView,
)

app_name = "invoices"

urlpatterns = [
    path("", InvoiceListCreateView.as_view(), name="invoice-list-create"),
    path("<uuid:invoice_id>/", InvoiceRetrieveUpdateDeleteView.as_view(), name="invoice-detail"),
    path("<uuid:invoice_id>/send/", InvoiceSendView.as_view(), name="invoice-send"),
    path("<uuid:invoice_id>/mark-paid/", InvoiceMarkPaidView.as_view(), name="invoice-mark-paid"),
    path("<uuid:invoice_id>/duplicate/", InvoiceDuplicateView.as_view(), name="invoice-duplicate"),
    path("<uuid:invoice_id>/events/", InvoiceEventsView.as_view(), name="invoice-events"),
    path("<uuid:invoice_id>/pdf/", InvoicePDFView.as_view(), name="invoice-pdf"),
]