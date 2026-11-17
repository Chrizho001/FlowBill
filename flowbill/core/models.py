import uuid6
from django.db import models


class TimeStampedModel(models.Model):
    """Adds created_at and updated_at to every model that inherits it."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet providing .active() to filter out soft-deleted rows."""

    def active(self):
        return self.filter(is_deleted=False)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Manager exposing .active() while preserving default queryset access."""


class SoftDeleteModel(models.Model):
    """
    Soft delete — records are never truly deleted.
    Call .delete() to soft delete, .restore() to recover.
    Use .objects.active() to get non-deleted records.
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


class UUIDModel(models.Model):
    """UUID7 primary key — time-ordered, unguessable."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid6.uuid7,
        editable=False,
    )

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """
    The standard base for all FlowBill tenant models.
    Combines UUID7 pk + timestamps + soft delete.
    """

    class Meta:
        abstract = True