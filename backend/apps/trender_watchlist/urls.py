from django.urls import path

from . import views

app_name = "trender_watchlist"

urlpatterns = [
    path("groups/", views.GroupListCreateView.as_view(), name="group-list"),
    path("groups/order/", views.GroupOrderView.as_view(), name="group-order"),
    path("groups/<int:group_id>/", views.GroupDetailView.as_view(), name="group-detail"),
    path("groups/<int:group_id>/items/", views.ItemListCreateView.as_view(), name="item-list"),
    path("groups/<int:group_id>/items/order/", views.ItemOrderView.as_view(), name="item-order"),
    path("groups/<int:group_id>/items/move/", views.ItemMoveView.as_view(), name="item-move"),
    path("groups/<int:group_id>/items/<int:stock_id>/", views.ItemDetailView.as_view(), name="item-detail"),
]
