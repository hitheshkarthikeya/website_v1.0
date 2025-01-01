from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),

]
