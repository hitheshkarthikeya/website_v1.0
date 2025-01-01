from django.shortcuts import render, redirect
from django.contrib import messages
from coupon.models import Coupon
from .models import Cart

def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            if not coupon.is_valid():
                messages.error(request, 'This coupon is not valid.')
                return redirect('cart:cart_detail')  # Adjust the URL name as per your URL config

            cart = Cart.objects.get(cart_id=_get_cart_id(request))
            if cart.coupon:
                messages.error(request, 'A coupon has already been applied.')
                return redirect('cart:cart_detail')

            # Check minimum amount
            cart_total = cart.total_with_discount()
            if cart_total < coupon.min_amount:
                messages.error(request, f'This coupon requires a minimum amount of {coupon.min_amount}.')
                return redirect('cart:cart_detail')

            # If coupon is user-specific, check if the user is allowed to use it
            if coupon.user and request.user != coupon.user:
                messages.error(request, 'You are not authorized to use this coupon.')
                return redirect('cart:cart_detail')

            # Apply the coupon
            cart.coupon = coupon
            cart.save()

            messages.success(request, 'Coupon applied successfully!')
            return redirect('cart:cart_detail')

        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
            return redirect('cart:cart_detail')

    return redirect('cart:cart_detail')

def _get_cart_id(request):
    cart_id = request.session.get('cart_id')
    if not cart_id:
        cart_id = _generate_cart_id()
        request.session['cart_id'] = cart_id
    return cart_id

def _generate_cart_id():
    import uuid
    return str(uuid.uuid4())
