from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Stock, StockQuote
from .serializers import StockQuoteSerializer, StockSerializer

SEARCH_RESULT_LIMIT = 20
PRICES_ID_LIMIT = 100


@extend_schema(
    tags=["stock"],
    summary="종목 검색",
    parameters=[
        OpenApiParameter("query", str, description="종목명 또는 코드 (부분 일치)"),
    ],
    responses={200: StockSerializer(many=True)},
)
class StockSearchView(generics.ListAPIView):
    serializer_class = StockSerializer
    pagination_class = None

    def get_queryset(self):
        query = self.request.query_params.get("query", "").strip()
        if not query:
            return Stock.objects.none()
        return Stock.objects.filter(is_active=True).filter(
            Q(name__icontains=query) | Q(code__istartswith=query) | Q(ticker__istartswith=query)
        )[:SEARCH_RESULT_LIMIT]


@extend_schema(
    tags=["stock"],
    summary="시세 묶음 조회",
    description="폴링용. 관심종목 화면 등에서 여러 종목의 현재 시세를 한 번에 조회한다.",
    parameters=[
        OpenApiParameter("ids", str, description=f"종목 id, 콤마로 구분 (예: 1,2,3, 최대 {PRICES_ID_LIMIT}개)"),
    ],
    responses={200: StockQuoteSerializer(many=True)},
)
class StockPricesView(APIView):
    def get(self, request):
        raw_ids = request.query_params.get("ids", "")
        raw_ids = [part for part in raw_ids.split(",") if part.strip()]

        try:
            ids = [int(part) for part in raw_ids]
        except ValueError:
            return Response(
                {"detail": "ids는 정수를 콤마로 구분한 목록이어야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(ids) > PRICES_ID_LIMIT:
            return Response(
                {"detail": f"ids는 한 번에 최대 {PRICES_ID_LIMIT}개까지 조회할 수 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not ids:
            return Response([])

        quotes = StockQuote.objects.filter(stock_id__in=ids)
        return Response(StockQuoteSerializer(quotes, many=True).data)
