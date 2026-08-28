from django.urls import path
from .views import ExpenseListCreateView, ExpenseRetrieveUpdateDeleteView

app_name = "expenses"

urlpatterns = [
    path("", ExpenseListCreateView.as_view(), name="expense-list-create"),
    path("<uuid:expense_id>/", ExpenseRetrieveUpdateDeleteView.as_view(), name="expense-detail"),
]