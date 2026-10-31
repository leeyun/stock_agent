from rest_framework import serializers

from apps.trender_stock.models import Stock
from apps.trender_stock.serializers import StockSerializer

from .models import WatchlistGroup, WatchlistItem


class WatchlistGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchlistGroup
        fields = ("id", "name", "is_default", "order")


class WatchlistGroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchlistGroup
        fields = ("id", "name")

    def validate_name(self, value):
        user = self.context["request"].user
        if WatchlistGroup.objects.filter(user=user, name=value).exists():
            raise serializers.ValidationError("이미 존재하는 그룹 이름입니다.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if WatchlistGroup.objects.filter(user=user).count() >= WatchlistGroup.MAX_GROUPS_PER_USER:
            raise serializers.ValidationError(
                f"그룹은 최대 {WatchlistGroup.MAX_GROUPS_PER_USER}개까지 만들 수 있습니다."
            )
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        next_order = WatchlistGroup.objects.filter(user=user).count()
        return WatchlistGroup.objects.create(user=user, order=next_order, **validated_data)


class WatchlistGroupRenameSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchlistGroup
        fields = ("name",)

    def validate_name(self, value):
        user = self.context["request"].user
        qs = WatchlistGroup.objects.filter(user=user, name=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("이미 존재하는 그룹 이름입니다.")
        return value


class GroupOrderSerializer(serializers.Serializer):
    order = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class WatchlistItemSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)

    class Meta:
        model = WatchlistItem
        fields = ("id", "stock", "order", "added_at")


class WatchlistItemCreateSerializer(serializers.Serializer):
    stock_id = serializers.IntegerField()

    def validate_stock_id(self, value):
        if not Stock.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("존재하지 않는 종목입니다.")
        group = self.context["group"]
        if WatchlistItem.objects.filter(group=group, stock_id=value).exists():
            raise serializers.ValidationError("이미 이 그룹에 추가된 종목입니다.")
        return value

    def validate(self, attrs):
        group = self.context["group"]
        if group.items.count() >= WatchlistItem.MAX_ITEMS_PER_GROUP:
            raise serializers.ValidationError(
                f"그룹당 종목은 최대 {WatchlistItem.MAX_ITEMS_PER_GROUP}개까지 추가할 수 있습니다."
            )
        return attrs


class ItemOrderSerializer(serializers.Serializer):
    order = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)  # stock_id 목록


class ItemMoveSerializer(serializers.Serializer):
    stock_id = serializers.IntegerField()
    target_group_id = serializers.IntegerField()
