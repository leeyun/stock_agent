from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from core.models import TimeStampModel


class WatchlistGroup(TimeStampModel):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="watchlist_groups")
    name       = models.CharField(max_length=30)
    is_default = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    MAX_GROUPS_PER_USER = 10

    class Meta:
        db_table = "watchlist_groups"
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"],
                                    name="uniq_group_name_per_user"),
            models.UniqueConstraint(fields=["user"], condition=Q(is_default=True),
                                    name="uniq_default_group_per_user"),
        ]
        indexes = [models.Index(fields=["user", "order"])]

    def delete(self, *args, **kwargs):
        if self.is_default:
            raise ValidationError("기본 그룹은 삭제할 수 없습니다.")
        return super().delete(*args, **kwargs)


class WatchlistItem(models.Model):
    group    = models.ForeignKey(WatchlistGroup, on_delete=models.CASCADE,
                                 related_name="items")
    stock    = models.ForeignKey("trender_stock.Stock", on_delete=models.CASCADE)
    order    = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    MAX_ITEMS_PER_GROUP = 50

    class Meta:
        db_table = "watchlist_items"
        ordering = ["order", "-added_at"]
        constraints = [
            models.UniqueConstraint(fields=["group", "stock"],
                                    name="uniq_stock_per_group"),
        ]
        indexes = [models.Index(fields=["group", "order"])]