from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WatchlistGroup

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_group(sender, instance, created, **kwargs):
    if created:
        WatchlistGroup.objects.create(
            user=instance, name="나의 관심종목", is_default=True, order=0
        )