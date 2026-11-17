from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import BasePermission


class DebugOrAdminPermission(BasePermission):
    """
    Allow open access to OpenAPI schema & Swagger UI in development/test;
    in production (EXPOSE_API_DOCS=False and DEBUG=False), restrict to
    authenticated staff/admin users.
    """

    def has_permission(self, request, view):
        if settings.DEBUG or getattr(settings, "EXPOSE_API_DOCS", False):
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls", namespace="accounts")),
    path("api/v1/clients/", include("apps.clients.urls", namespace="clients")),
    path("api/v1/invoices/", include("apps.invoices.urls", namespace="invoices")),
    path("api/v1/dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("api/v1/expenses/", include("apps.expenses.urls", namespace="expenses")),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=[DebugOrAdminPermission]),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            permission_classes=[DebugOrAdminPermission],
        ),
        name="swagger-ui",
    ),
]
