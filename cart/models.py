from django.db import models

from shop.models import Product
from shop.models import Variation
from accounts.models import Account

from coupon.models import Coupon

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    create = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.cart_id

    def total_with_discount(self):
        total = sum(item.sub_total() for item in self.cartitem_set.all() if item.is_active)
        if self.coupon and self.coupon.is_valid():
            discount = 0
            if self.coupon.discount_type == 'percentage':
                discount = (self.coupon.discount_value / 100) * total
                if self.coupon.max_discount:
                    discount = min(discount, self.coupon.max_discount)
            elif self.coupon.discount_type == 'fixed':
                discount = self.coupon.discount_value
            total -= discount
            return max(total, 0)
        return total


class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product.price * self.quantity

    def __unicode__(self):
        return self.product
    