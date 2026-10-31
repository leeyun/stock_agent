from django.apps import AppConfig

class StocksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trender_stock"        # 점 표기 전체 경로
    label = "trender_stock"            # 마이그레이션·FK 참조에 쓰이는 짧은 이름