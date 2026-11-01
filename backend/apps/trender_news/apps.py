from django.apps import AppConfig


class TrenderNewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trender_news"

    def ready(self):
        from . import signals  # noqa: F401  관심종목 추가 시 뉴스 수집 예약
