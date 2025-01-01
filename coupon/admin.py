from django.contrib import admin
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'description',
        'discount_type',
        'discount_value',
        'min_amount',
        'max_discount',
        'active',
        'valid_from',
        'valid_to',
        'usage_limit',
        'used_count',
        'user',
    )
    list_filter = ('discount_type', 'active', 'valid_from', 'valid_to')
    search_fields = ('code', 'description')
    readonly_fields = ('used_count',)

    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'discount_type', 'discount_value')
        }),
        ('Usage', {
            'fields': ('min_amount', 'max_discount', 'usage_limit', 'used_count')
        }),
        ('Validity', {
            'fields': ('active', 'valid_from', 'valid_to')
        }),
        ('User Restriction', {
            'fields': ('user',)
        }),
    )

    def has_change_permission(self, request, obj=None):
        if obj and obj.used_count >= obj.usage_limit:
            return False  # Prevent editing if usage limit reached
        return super().has_change_permission(request, obj)
