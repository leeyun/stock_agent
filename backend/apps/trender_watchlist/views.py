from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import ZeroIndexedPageNumberPagination

from .models import WatchlistGroup, WatchlistItem
from .serializers import (
    GroupOrderSerializer, ItemMoveSerializer, ItemOrderSerializer,
    WatchlistGroupCreateSerializer, WatchlistGroupRenameSerializer, WatchlistGroupSerializer,
    WatchlistItemCreateSerializer, WatchlistItemSerializer,
)


def _get_owned_group(user, group_id):
    return get_object_or_404(WatchlistGroup, pk=group_id, user=user)


@extend_schema(tags=["watchlist"])
class GroupListCreateView(generics.ListCreateAPIView):
    pagination_class = None

    def get_queryset(self):
        return WatchlistGroup.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return WatchlistGroupCreateSerializer if self.request.method == "POST" else WatchlistGroupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(WatchlistGroupSerializer(group).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["watchlist"], summary="그룹 순서 변경",
    request=GroupOrderSerializer, responses={200: WatchlistGroupSerializer(many=True)},
)
class GroupOrderView(APIView):
    def patch(self, request):
        serializer = GroupOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ordered_ids = serializer.validated_data["order"]

        groups = {g.id: g for g in WatchlistGroup.objects.filter(user=request.user, id__in=ordered_ids)}
        if set(groups.keys()) != set(ordered_ids):
            return Response(
                {"detail": "order 목록에 존재하지 않거나 소유하지 않은 그룹 id가 포함되어 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = []
        for index, group_id in enumerate(ordered_ids):
            group = groups[group_id]
            group.order = index
            updated.append(group)
        WatchlistGroup.objects.bulk_update(updated, ["order"])

        return Response(WatchlistGroupSerializer(updated, many=True).data)


@extend_schema_view(
    patch=extend_schema(
        tags=["watchlist"], summary="그룹 이름 변경",
        request=WatchlistGroupRenameSerializer, responses={200: WatchlistGroupSerializer},
    ),
    delete=extend_schema(
        tags=["watchlist"], summary="그룹 삭제",
        request=None,
        responses={204: None, 400: OpenApiResponse(description="기본 그룹은 삭제할 수 없음")},
    ),
)
class GroupDetailView(APIView):
    def patch(self, request, group_id):
        group = _get_owned_group(request.user, group_id)
        serializer = WatchlistGroupRenameSerializer(group, data=request.data, partial=True,
                                                      context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(WatchlistGroupSerializer(group).data)

    def delete(self, request, group_id):
        group = _get_owned_group(request.user, group_id)
        if group.is_default:
            return Response({"detail": "기본 그룹은 삭제할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["watchlist"])
class ItemListCreateView(generics.ListCreateAPIView):
    pagination_class = ZeroIndexedPageNumberPagination

    def get_group(self):
        return _get_owned_group(self.request.user, self.kwargs["group_id"])

    def get_queryset(self):
        return WatchlistItem.objects.filter(group=self.get_group()).select_related("stock")

    def get_serializer_class(self):
        return WatchlistItemCreateSerializer if self.request.method == "POST" else WatchlistItemSerializer

    def create(self, request, *args, **kwargs):
        group = self.get_group()
        serializer = WatchlistItemCreateSerializer(data=request.data, context={"group": group})
        serializer.is_valid(raise_exception=True)

        item = WatchlistItem.objects.create(
            group=group,
            stock_id=serializer.validated_data["stock_id"],
            order=group.items.count(),
        )
        return Response(WatchlistItemSerializer(item).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["watchlist"], summary="종목 순서 변경 (stock_id 목록)",
    request=ItemOrderSerializer, responses={200: WatchlistItemSerializer(many=True)},
)
class ItemOrderView(APIView):
    def patch(self, request, group_id):
        group = _get_owned_group(request.user, group_id)
        serializer = ItemOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ordered_stock_ids = serializer.validated_data["order"]

        items = {i.stock_id: i for i in WatchlistItem.objects.filter(group=group, stock_id__in=ordered_stock_ids)}
        if set(items.keys()) != set(ordered_stock_ids):
            return Response(
                {"detail": "order 목록에 이 그룹에 없는 stock_id가 포함되어 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = []
        for index, stock_id in enumerate(ordered_stock_ids):
            item = items[stock_id]
            item.order = index
            updated.append(item)
        WatchlistItem.objects.bulk_update(updated, ["order"])

        return Response(WatchlistItemSerializer(updated, many=True).data)


@extend_schema(
    tags=["watchlist"], summary="다른 그룹으로 이동",
    request=ItemMoveSerializer, responses={200: WatchlistItemSerializer},
)
class ItemMoveView(APIView):
    def post(self, request, group_id):
        source_group = _get_owned_group(request.user, group_id)
        serializer = ItemMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stock_id = serializer.validated_data["stock_id"]
        target_group_id = serializer.validated_data["target_group_id"]

        if target_group_id == source_group.id:
            return Response({"detail": "출발 그룹과 도착 그룹이 같습니다."}, status=status.HTTP_400_BAD_REQUEST)

        target_group = _get_owned_group(request.user, target_group_id)
        item = get_object_or_404(WatchlistItem, group=source_group, stock_id=stock_id)

        if WatchlistItem.objects.filter(group=target_group, stock_id=stock_id).exists():
            return Response({"detail": "이미 대상 그룹에 추가된 종목입니다."}, status=status.HTTP_400_BAD_REQUEST)
        if target_group.items.count() >= WatchlistItem.MAX_ITEMS_PER_GROUP:
            return Response(
                {"detail": f"그룹당 종목은 최대 {WatchlistItem.MAX_ITEMS_PER_GROUP}개까지 추가할 수 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.group = target_group
        item.order = target_group.items.count()
        item.save(update_fields=["group", "order"])

        return Response(WatchlistItemSerializer(item).data)


@extend_schema(tags=["watchlist"], summary="종목 제거", request=None, responses={204: None})
class ItemDetailView(APIView):
    def delete(self, request, group_id, stock_id):
        group = _get_owned_group(request.user, group_id)
        item = get_object_or_404(WatchlistItem, group=group, stock_id=stock_id)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
