from django.db import models
from django.utils import timezone
from accounts.models import Account

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(
        max_length=10,
        choices=(
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed Amount'),
        )
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    usage_limit = models.IntegerField(default=1)  # Total number of times the coupon can be used
    used_count = models.IntegerField(default=0)   # Number of times the coupon has been used
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, help_text="If set, only this user can use the coupon.")

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if self.active and self.valid_from <= now <= self.valid_to:
            if self.usage_limit > self.used_count:
                return True
        return False

    def increment_usage(self):
        self.used_count += 1
        self.save()
