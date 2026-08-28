import structlog
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth

logger = structlog.get_logger(__name__)


class DashboardService:
    """
    Aggregated analytics queries for the dashboard.
    All queries are filtered by owner — never leak cross-user data.
    All monetary aggregations use Decimal with proper defaults.
    """

    @staticmethod
    def get_stats(user) -> dict:
        """Returns the 4 summary stat cards for the dashboard."""
        from apps.invoices.models import Invoice
        from apps.clients.models import Client

        invoices = Invoice.objects.filter(owner=user, is_deleted=False)

        aggregates = invoices.aggregate(
            total_earned=Sum("total", filter=Q(status="paid")),
            total_pending=Sum("total", filter=Q(status="pending")),
            total_overdue=Sum("total", filter=Q(status="overdue")),
            pending_count=Count("id", filter=Q(status="pending")),
            overdue_count=Count("id", filter=Q(status="overdue")),
        )

        active_clients = Client.objects.filter(
            owner=user,
            status="active",
            is_deleted=False,
        ).count()

        # Get invoices created this month
        today = date.today()
        invoices_this_month = invoices.filter(
            created_at__year=today.year,
            created_at__month=today.month,
        ).count()

        return {
            "total_earned": aggregates["total_earned"] or Decimal("0.00"),
            "total_pending": aggregates["total_pending"] or Decimal("0.00"),
            "total_overdue": aggregates["total_overdue"] or Decimal("0.00"),
            "active_clients": active_clients,
            "pending_count": aggregates["pending_count"] or 0,
            "overdue_count": aggregates["overdue_count"] or 0,
            "invoices_this_month": invoices_this_month,
        }

    @staticmethod
    def get_revenue_chart(user, months: int = 6) -> dict:
        """
        Returns monthly revenue (paid invoices only) for the last N months.
        Always returns exactly N data points even if some months have zero revenue.
        """
        from apps.invoices.models import Invoice

        # Cap months between 1 and 12
        months = max(1, min(months, 12))

        today = date.today()

        # Build list of last N months
        month_list = []
        for i in range(months - 1, -1, -1):
            # Go back i months from today
            month_date = today.replace(day=1)
            total_months_back = i
            year = month_date.year
            month = month_date.month - total_months_back
            while month <= 0:
                month += 12
                year -= 1
            month_list.append((year, month))

        # Query paid invoices grouped by month
        revenue_by_month = Invoice.objects.filter(
            owner=user,
            status="paid",
            is_deleted=False,
            issue_date__gte=date(month_list[0][0], month_list[0][1], 1),
        ).annotate(
            month=TruncMonth("issue_date")
        ).values("month").annotate(
            total=Sum("total")
        ).order_by("month")

        # Build lookup dict from query results
        revenue_lookup = {
            (entry["month"].year, entry["month"].month): entry["total"]
            for entry in revenue_by_month
        }

        # Build ordered labels and data arrays
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        labels = []
        data = []

        for year, month in month_list:
            labels.append(f"{month_names[month - 1]} {year}")
            revenue = revenue_lookup.get((year, month), Decimal("0.00"))
            data.append(float(revenue))

        return {"labels": labels, "data": data}

    @staticmethod
    def get_top_clients(user, limit: int = 5) -> list:
        """
        Returns top N clients by total billed amount across all invoice statuses
        except draft and cancelled.
        """
        from apps.invoices.models import Invoice

        limit = max(1, min(limit, 20))

        results = Invoice.objects.filter(
            owner=user,
            is_deleted=False,
            status__in=("paid", "pending", "overdue"),
        ).values(
            "client__id",
            "client__name",
            "client__company_name",
        ).annotate(
            total_billed=Sum("total"),
            invoice_count=Count("id"),
        ).order_by("-total_billed")[:limit]

        # Calculate total across all clients for percentage
        all_total = sum(r["total_billed"] for r in results) or Decimal("1.00")

        return [
            {
                "client_id": str(r["client__id"]),
                "name": r["client__name"],
                "company": r["client__company_name"] or "",
                "total_billed": r["total_billed"],
                "invoice_count": r["invoice_count"],
                "percentage": round(float(r["total_billed"] / all_total * 100), 1),
            }
            for r in results
        ]

    @staticmethod
    def get_upcoming_due(user, days: int = 7) -> list:
        """
        Returns pending and overdue invoices due within the next N days.
        Sorted by due date ascending — most urgent first.
        """
        from apps.invoices.models import Invoice

        today = date.today()
        cutoff = today + timedelta(days=days)

        invoices = Invoice.objects.filter(
            owner=user,
            is_deleted=False,
            status__in=("pending", "overdue"),
            due_date__gte=today,
            due_date__lte=cutoff,
        ).select_related("client").order_by("due_date")

        return [
            {
                "invoice_id": str(inv.id),
                "number": inv.number,
                "client_name": inv.client.name,
                "client_company": inv.client.company_name or "",
                "amount": inv.total,
                "due_date": inv.due_date,
                "days_until_due": (inv.due_date - today).days,
                "status": inv.status,
            }
            for inv in invoices
        ]