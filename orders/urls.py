from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('payment-method/', views.payment_method, name='payment_method'),
    path('checkout/', views.checkout, name='checkout'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('payment/', views.payment, name='payment'),
    path('payments/', views.payments, name='payments'),
    path('order-completed/', views.order_completed, name='order_completed'),
    # Add other URL patterns as needed
]
