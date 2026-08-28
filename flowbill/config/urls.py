from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls", namespace="accounts")),
    path("api/v1/clients/", include("apps.clients.urls", namespace="clients")),
    path("api/v1/invoices/", include("apps.invoices.urls", namespace="invoices")),
    path("api/v1/dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("api/v1/expenses/", include("apps.expenses.urls", namespace="expenses")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
