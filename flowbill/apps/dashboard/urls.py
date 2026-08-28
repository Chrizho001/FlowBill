from django.urls import path
from .views import (
    DashboardStatsView,
    RevenueChartView,
    TopClientsView,
    UpcomingDueView,
)

app_name = "dashboard"

urlpatterns = [
    path("stats/", DashboardStatsView.as_view(), name="stats"),
    path("revenue-chart/", RevenueChartView.as_view(), name="revenue-chart"),
    path("top-clients/", TopClientsView.as_view(), name="top-clients"),
    path("upcoming-due/", UpcomingDueView.as_view(), name="upcoming-due"),
]