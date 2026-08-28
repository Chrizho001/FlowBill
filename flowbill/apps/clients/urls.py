from django.urls import path
from .views import ClientListCreateView, ClientRetrieveUpdateDeleteView

app_name = "clients"

urlpatterns = [
    path("", ClientListCreateView.as_view(), name="client-list-create"),
    path("<uuid:client_id>/", ClientRetrieveUpdateDeleteView.as_view(), name="client-detail"),
]