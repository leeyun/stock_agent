from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.trender_stock.models import Market, Stock

from .models import WatchlistGroup, WatchlistItem

User = get_user_model()


class WatchlistTestBase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", email="u1@example.com", password="pw12345!")
        self.other = User.objects.create_user(username="u2", email="u2@example.com", password="pw12345!")
        self.client.force_authenticate(self.user)
        # 시그널로 기본 그룹이 자동 생성됨
        self.default_group = WatchlistGroup.objects.get(user=self.user, is_default=True)

        self.samsung = Stock.objects.create(code="005930", ticker="005930.KS", name="삼성전자", market=Market.KOSPI)
        self.sk = Stock.objects.create(code="000660", ticker="000660.KS", name="SK하이닉스", market=Market.KOSPI)


class GroupTests(WatchlistTestBase):
    def test_list_shows_only_own_groups(self):
        WatchlistGroup.objects.create(user=self.other, name="다른유저그룹", order=0)
        res = self.client.get(reverse("trender_watchlist:group-list"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["name"], self.default_group.name)

    def test_create_group(self):
        res = self.client.post(reverse("trender_watchlist:group-list"), {"name": "성장주"})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["order"], 1)
        self.assertFalse(res.json()["is_default"])

    def test_create_group_duplicate_name_rejected(self):
        res = self.client.post(reverse("trender_watchlist:group-list"), {"name": self.default_group.name})
        self.assertEqual(res.status_code, 400)

    def test_create_group_over_limit_rejected(self):
        for i in range(WatchlistGroup.MAX_GROUPS_PER_USER - 1):
            WatchlistGroup.objects.create(user=self.user, name=f"g{i}", order=i + 1)
        res = self.client.post(reverse("trender_watchlist:group-list"), {"name": "초과그룹"})
        self.assertEqual(res.status_code, 400)

    def test_rename_group(self):
        url = reverse("trender_watchlist:group-detail", args=[self.default_group.id])
        res = self.client.patch(url, {"name": "새이름"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "새이름")

    def test_cannot_rename_other_users_group(self):
        other_group = WatchlistGroup.objects.create(user=self.other, name="남의그룹", order=0)
        url = reverse("trender_watchlist:group-detail", args=[other_group.id])
        res = self.client.patch(url, {"name": "훔친이름"})
        self.assertEqual(res.status_code, 404)

    def test_delete_default_group_rejected(self):
        url = reverse("trender_watchlist:group-detail", args=[self.default_group.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 400)
        self.assertTrue(WatchlistGroup.objects.filter(pk=self.default_group.id).exists())

    def test_delete_non_default_group(self):
        group = WatchlistGroup.objects.create(user=self.user, name="지울그룹", order=1)
        url = reverse("trender_watchlist:group-detail", args=[group.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(WatchlistGroup.objects.filter(pk=group.id).exists())

    def test_reorder_groups(self):
        g2 = WatchlistGroup.objects.create(user=self.user, name="g2", order=1)
        g3 = WatchlistGroup.objects.create(user=self.user, name="g3", order=2)
        url = reverse("trender_watchlist:group-order")
        res = self.client.patch(url, {"order": [g3.id, self.default_group.id, g2.id]}, format="json")
        self.assertEqual(res.status_code, 200)
        self.default_group.refresh_from_db()
        g2.refresh_from_db()
        g3.refresh_from_db()
        self.assertEqual((g3.order, self.default_group.order, g2.order), (0, 1, 2))

    def test_reorder_rejects_foreign_id(self):
        other_group = WatchlistGroup.objects.create(user=self.other, name="남의그룹", order=0)
        url = reverse("trender_watchlist:group-order")
        res = self.client.patch(url, {"order": [self.default_group.id, other_group.id]}, format="json")
        self.assertEqual(res.status_code, 400)


class ItemTests(WatchlistTestBase):
    def items_url(self, group=None):
        return reverse("trender_watchlist:item-list", args=[(group or self.default_group).id])

    def test_add_item(self):
        res = self.client.post(self.items_url(), {"stock_id": self.samsung.id})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["stock"]["code"], "005930")

    def test_add_duplicate_item_rejected(self):
        WatchlistItem.objects.create(group=self.default_group, stock=self.samsung, order=0)
        res = self.client.post(self.items_url(), {"stock_id": self.samsung.id})
        self.assertEqual(res.status_code, 400)

    def test_add_item_over_limit_rejected(self):
        stocks = [
            Stock.objects.create(code=f"{i:06d}", ticker=f"{i:06d}.KS", name=f"종목{i}", market=Market.KOSPI)
            for i in range(WatchlistItem.MAX_ITEMS_PER_GROUP)
        ]
        WatchlistItem.objects.bulk_create([
            WatchlistItem(group=self.default_group, stock=s, order=i) for i, s in enumerate(stocks)
        ])
        res = self.client.post(self.items_url(), {"stock_id": self.samsung.id})
        self.assertEqual(res.status_code, 400)

    def test_cannot_add_item_to_others_group(self):
        other_group = WatchlistGroup.objects.create(user=self.other, name="남의그룹", order=0)
        res = self.client.post(self.items_url(other_group), {"stock_id": self.samsung.id})
        self.assertEqual(res.status_code, 404)

    def test_list_items_paginated(self):
        WatchlistItem.objects.create(group=self.default_group, stock=self.samsung, order=0)
        WatchlistItem.objects.create(group=self.default_group, stock=self.sk, order=1)
        res = self.client.get(self.items_url(), {"page": 0, "size": 1})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["count"], 2)

    def test_remove_item(self):
        WatchlistItem.objects.create(group=self.default_group, stock=self.samsung, order=0)
        url = reverse("trender_watchlist:item-detail", args=[self.default_group.id, self.samsung.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(WatchlistItem.objects.filter(group=self.default_group, stock=self.samsung).exists())

    def test_reorder_items(self):
        WatchlistItem.objects.create(group=self.default_group, stock=self.samsung, order=0)
        WatchlistItem.objects.create(group=self.default_group, stock=self.sk, order=1)
        url = reverse("trender_watchlist:item-order", args=[self.default_group.id])
        res = self.client.patch(url, {"order": [self.sk.id, self.samsung.id]}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            WatchlistItem.objects.get(group=self.default_group, stock=self.sk).order, 0,
        )

    def test_move_item_to_another_group(self):
        WatchlistItem.objects.create(group=self.default_group, stock=self.samsung, order=0)
        target = WatchlistGroup.objects.create(user=self.user, name="타겟", order=1)
        url = reverse("trender_watchlist:item-move", args=[self.default_group.id])
        res = self.client.post(url, {"stock_id": self.samsung.id, "target_group_id": target.id}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(WatchlistItem.objects.filter(group=self.default_group, stock=self.samsung).exists())
        self.assertTrue(WatchlistItem.objects.filter(group=target, stock=self.samsung).exists())

    def test_move_item_to_others_group_rejected(self):
        WatchlistItem.objects.create(group=self.default_group, stock=self.samsung, order=0)
        other_group = WatchlistGroup.objects.create(user=self.other, name="남의그룹", order=0)
        url = reverse("trender_watchlist:item-move", args=[self.default_group.id])
        res = self.client.post(url, {"stock_id": self.samsung.id, "target_group_id": other_group.id}, format="json")
        self.assertEqual(res.status_code, 404)
