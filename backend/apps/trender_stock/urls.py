from django.urls import path

from .views import StockPricesView, StockSearchView

app_name = "trender_stock"

urlpatterns = [
    path("", StockSearchView.as_view(), name="search"),
    path("prices/", StockPricesView.as_view(), name="prices"),
]
