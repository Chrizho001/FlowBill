import structlog
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import ClientSerializer, ClientListSerializer
from .services import ClientService
from .models import Client
from core.pagination import StandardPagination

logger = structlog.get_logger(__name__)


class ClientListCreateView(APIView):
    """
    GET  /api/v1/clients/  — list all clients for the authenticated user
    POST /api/v1/clients/  — create a new client
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get("search")
        status_filter = request.query_params.get("status")

        clients = ClientService.get_clients(
            user=request.user,
            search=search,
            status=status_filter,
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(clients, request)
        serializer = ClientListSerializer(page, many=True)

        logger.info(
            "clients.list.success",
            user_id=str(request.user.id),
            count=len(page),
            search=search,
            status_filter=status_filter,
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client = ClientService.create_client(
            user=request.user,
            validated_data=serializer.validated_data,
        )

        logger.info(
            "clients.create.success",
            user_id=str(request.user.id),
            client_id=str(client.id),
            client_email=client.email,
        )

        return Response({
            "status": "success",
            "message": "Client created successfully.",
            "data": ClientSerializer(client).data,
        }, status=status.HTTP_201_CREATED)


class ClientRetrieveUpdateDeleteView(APIView):
    """
    GET    /api/v1/clients/{id}/  — retrieve a single client
    PATCH  /api/v1/clients/{id}/  — update a client
    DELETE /api/v1/clients/{id}/  — soft delete a client
    """
    permission_classes = [IsAuthenticated]

    def get_client(self, request, client_id):
        """Helper — returns client or raises 404."""
        try:
            return ClientService.get_client(request.user, client_id)
        except Client.DoesNotExist:
            logger.warning(
                "clients.not_found",
                user_id=str(request.user.id),
                client_id=str(client_id),
            )
            return None

    def get(self, request, client_id):
        client = self.get_client(request, client_id)
        if not client:
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Client not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        logger.info(
            "clients.retrieve.success",
            user_id=str(request.user.id),
            client_id=str(client.id),
        )

        return Response({
            "status": "success",
            "data": ClientSerializer(client).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, client_id):
        client = self.get_client(request, client_id)
        if not client:
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Client not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ClientSerializer(client, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_client = ClientService.update_client(
            client=client,
            validated_data=serializer.validated_data,
        )

        logger.info(
            "clients.update.success",
            user_id=str(request.user.id),
            client_id=str(updated_client.id),
            fields_changed=list(serializer.validated_data.keys()),
        )

        return Response({
            "status": "success",
            "message": "Client updated successfully.",
            "data": ClientSerializer(updated_client).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request, client_id):
        client = self.get_client(request, client_id)
        if not client:
            return Response({
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Client not found.",
                "fields": {},
            }, status=status.HTTP_404_NOT_FOUND)

        ClientService.delete_client(client)

        logger.info(
            "clients.delete.success",
            user_id=str(request.user.id),
            client_id=str(client.id),
        )

        return Response({
            "status": "success",
            "message": "Client deleted successfully.",
        }, status=status.HTTP_200_OK)