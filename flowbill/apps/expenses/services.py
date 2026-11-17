import structlog
from django.db.models import QuerySet
from rest_framework import serializers
from .models import Expense

logger = structlog.get_logger(__name__)


class ExpenseService:
    """All business logic for expense management."""

    @staticmethod
    def _validate_client_ownership(owner, client) -> None:
        if client is not None and (client.owner_id != owner.id or client.is_deleted):
            raise serializers.ValidationError({
                "client": "Client not found or does not belong to you."
            })

    @staticmethod
    def get_expenses(user, category: str = None, client_id: str = None) -> QuerySet:
        queryset = Expense.objects.filter(
            owner=user,
            is_deleted=False,
        ).select_related("client")

        if category:
            queryset = queryset.filter(category=category)

        if client_id:
            queryset = queryset.filter(client_id=client_id)

        return queryset.order_by("-date", "-created_at")

    @staticmethod
    def get_expense(user, expense_id: str) -> Expense:
        return Expense.objects.get(
            id=expense_id,
            owner=user,
            is_deleted=False,
        )

    @staticmethod
    def create_expense(user, validated_data: dict) -> Expense:
        ExpenseService._validate_client_ownership(user, validated_data.get("client"))
        expense = Expense.objects.create(owner=user, **validated_data)
        logger.info(
            "expenses.created",
            expense_id=str(expense.id),
            owner_id=str(user.id),
            amount=str(expense.amount),
            category=expense.category,
        )
        return expense

    @staticmethod
    def update_expense(expense: Expense, validated_data: dict) -> Expense:
        if "client" in validated_data:
            ExpenseService._validate_client_ownership(expense.owner, validated_data.get("client"))
        for field, value in validated_data.items():
            setattr(expense, field, value)
        expense.save()
        logger.info("expenses.updated", expense_id=str(expense.id))
        return expense

    @staticmethod
    def delete_expense(expense: Expense) -> None:
        expense.delete()
        logger.info("expenses.deleted", expense_id=str(expense.id))