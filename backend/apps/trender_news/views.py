from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from core.pagination import ZeroIndexedPageNumberPagination
from .models import StockNews
from .serializers import NewsDetailSerializer

class StockNewsListView(generics.ListAPIView):
    serializer_class = NewsDetailSerializer
    pagination_class = ZeroIndexedPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = StockNews.objects.select_related("news", "stock").order_by("-news__published_at")
        stock_id = self.request.query_params.get("stock_id")
        if stock_id:
            qs = qs.filter(stock_id=stock_id)
        return qs
