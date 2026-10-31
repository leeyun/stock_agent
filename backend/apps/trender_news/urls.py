from django.urls import path
from .views import StockNewsListView

app_name = "trender_news"

urlpatterns = [
    path("", StockNewsListView.as_view(), name="news-list"),
]
