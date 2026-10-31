# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ("username", "email", "is_staff", "created_at")
    search_fields = ("username", "email")
    ordering      = ("-created_at",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("추가 정보", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")