from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AccessHistory, Entitlement, Product, PurchaseHistory, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("Extra", {"fields": ("address", "role")}),)
    list_display = ('email', 'username', 'role', 'is_staff')


admin.site.register(Product)
admin.site.register(Entitlement)
admin.site.register(PurchaseHistory)
admin.site.register(AccessHistory)
