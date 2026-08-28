import structlog
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import DashboardService

logger = structlog.get_logger(__name__)


class DashboardStatsView(APIView):
    """GET /api/v1/dashboard/stats/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = DashboardService.get_stats(request.user)
        return Response({
            "status": "success",
            "data": {
                "total_earned": str(stats["total_earned"]),
                "total_pending": str(stats["total_pending"]),
                "total_overdue": str(stats["total_overdue"]),
                "active_clients": stats["active_clients"],
                "pending_count": stats["pending_count"],
                "overdue_count": stats["overdue_count"],
                "invoices_this_month": stats["invoices_this_month"],
            },
        }, status=status.HTTP_200_OK)


class RevenueChartView(APIView):
    """GET /api/v1/dashboard/revenue-chart/?months=6"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            months = int(request.query_params.get("months", 6))
        except (ValueError, TypeError):
            months = 6

        chart_data = DashboardService.get_revenue_chart(request.user, months)

        return Response({
            "status": "success",
            "data": chart_data,
        }, status=status.HTTP_200_OK)


class TopClientsView(APIView):
    """GET /api/v1/dashboard/top-clients/?limit=5"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 5))
        except (ValueError, TypeError):
            limit = 5

        clients = DashboardService.get_top_clients(request.user, limit)

        return Response({
            "status": "success",
            "data": [
                {
                    **c,
                    "total_billed": str(c["total_billed"]),
                    "amount": str(c["total_billed"]),
                }
                for c in clients
            ],
        }, status=status.HTTP_200_OK)


class UpcomingDueView(APIView):
    """GET /api/v1/dashboard/upcoming-due/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 7))
        except (ValueError, TypeError):
            days = 7

        invoices = DashboardService.get_upcoming_due(request.user, days)

        return Response({
            "status": "success",
            "data": [
                {
                    **inv,
                    "amount": str(inv["amount"]),
                    "due_date": str(inv["due_date"]),
                }
                for inv in invoices
            ],
        }, status=status.HTTP_200_OK)