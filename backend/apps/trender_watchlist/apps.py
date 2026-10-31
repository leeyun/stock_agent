# apps/trender_watchlist/apps.py
from django.apps import AppConfig


class TrenderWatchlistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trender_watchlist"      # 폴더 구조상 apps. 접두사 필요

    def ready(self):
        from . import signals            # noqa: F401