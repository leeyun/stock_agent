# config/urls.py
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # authentication urls
    path("api/auth/", include("apps.trender_auth.urls")),

    # TODO: user urls

    # apps urls
    path("api/stock/", include("apps.trender_stock.urls")),
    path("api/watchlist/", include("apps.trender_watchlist.urls")),
    path("api/news/", include("apps.trender_news.urls")),

    # Swagger-ui schema urls
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]