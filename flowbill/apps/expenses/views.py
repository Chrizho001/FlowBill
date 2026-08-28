import structlog
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Expense
from .serializers import ExpenseSerializer, ExpenseListSerializer
from .services import ExpenseService
from core.pagination import StandardPagination

logger = structlog.get_logger(__name__)


class ExpenseListCreateView(APIView):
    """
    GET  /api/v1/expenses/  — list all expenses
    POST /api/v1/expenses/  — create a new expense
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get("category")
        client_id = request.query_params.get("client")

        expenses = ExpenseService.get_expenses(
            user=request.user,
            category=category,
            client_id=client_id,
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(expenses, request)
        serializer = ExpenseListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        expense = ExpenseService.create_expense(
            user=request.user,
            validated_data=serializer.validated_data,
        )

        return Response({
            "status": "success",
            "message": "Expense recorded successfully.",
            "data": ExpenseSerializer(expense).data,
        }, status=status.HTTP_201_CREATED)


class ExpenseRetrieveUpdateDeleteView(APIView):
    """
    GET    /api/v1/expenses/{id}/
    PATCH  /api/v1/expenses/{id}/
    DELETE /api/v1/expenses/{id}/
    """
    permission_classes = [IsAuthenticated]

    def get_expense(self, request, expense_id):
        try:
            return ExpenseService.get_expense(request.user, expense_id)
        except Expense.DoesNotExist:
            return None

    def get(self, request, expense_id):
        expense = self.get_expense(request, expense_id)
        if not expense:
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Expense not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "status": "success",
            "data": ExpenseSerializer(expense).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, expense_id):
        expense = self.get_expense(request, expense_id)
        if not expense:
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Expense not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ExpenseSerializer(expense, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = ExpenseService.update_expense(
            expense=expense,
            validated_data=serializer.validated_data,
        )

        return Response({
            "status": "success",
            "message": "Expense updated successfully.",
            "data": ExpenseSerializer(updated).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request, expense_id):
        expense = self.get_expense(request, expense_id)
        if not expense:
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Expense not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        ExpenseService.delete_expense(expense)

        return Response({
            "status": "success",
            "message": "Expense deleted successfully.",
        }, status=status.HTTP_200_OK)