import structlog
from django.db import IntegrityError
from django.db.models import QuerySet
from rest_framework import serializers
from .models import Client

logger = structlog.get_logger(__name__)


class ClientService:
    """All business logic for client management."""

    @staticmethod
    def get_clients(user, search: str = None, status: str = None) -> QuerySet:
        """
        Returns all active (non-deleted) clients for a given user.
        Optionally filters by search term and/or status.
        """
        queryset = Client.objects.filter(
            owner=user,
            is_deleted=False,
        )

        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(company_name__icontains=search)
            )

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-created_at")

    @staticmethod
    def get_client(user, client_id: str) -> Client:
        """
        Retrieves a single client by ID — must belong to the user.
        Raises Client.DoesNotExist if not found or not owned by user.
        """
        client = Client.objects.get(
            id=client_id,
            owner=user,
            is_deleted=False,
        )
        logger.info("clients.retrieved", client_id=str(client.id), owner_id=str(user.id))
        return client

    @staticmethod
    def create_client(user, validated_data: dict) -> Client:
        """
        Creates a new client for the given user.
        Raises ValidationError if email already exists for this owner.
        """
        try:
            client = Client.objects.create(
                owner=user,
                **validated_data,
            )
            logger.info(
                "clients.created",
                client_id=str(client.id),
                owner_id=str(user.id),
                email=client.email,
            )
            return client
        except IntegrityError:
            logger.warning(
                "clients.create.duplicate_email",
                owner_id=str(user.id),
                email=validated_data.get("email", ""),
            )
            raise serializers.ValidationError({
                "email": "A client with this email already exists."
            })

    @staticmethod
    def update_client(client: Client, validated_data: dict) -> Client:
        """
        Updates an existing client with new data.
        Raises ValidationError if updated email conflicts with existing client.
        """
        try:
            for field, value in validated_data.items():
                setattr(client, field, value)
            client.save()
            logger.info(
                "clients.updated",
                client_id=str(client.id),
                owner_id=str(client.owner_id),
            )
            return client
        except IntegrityError:
            logger.warning(
                "clients.update.duplicate_email",
                client_id=str(client.id),
                owner_id=str(client.owner_id),
            )
            raise serializers.ValidationError({
                "email": "A client with this email already exists."
            })

    @staticmethod
    def delete_client(client: Client) -> None:
        """
        Soft deletes a client.
        Raises ValidationError if client has outstanding unpaid invoices.
        """
        from apps.invoices.models import Invoice

        has_unpaid_invoices = Invoice.objects.filter(
            client=client,
            is_deleted=False,
            status__in=("pending", "overdue"),
        ).exists()
        if has_unpaid_invoices:
            raise serializers.ValidationError(
                "Cannot delete a client with outstanding unpaid invoices."
            )

        client.delete()
        logger.info(
            "clients.deleted",
            client_id=str(client.id),
            owner_id=str(client.owner_id),
        )