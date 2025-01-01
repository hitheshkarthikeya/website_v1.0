import json
import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse
from django.contrib import messages

from cart.models import CartItem, Cart
from cart.views import _cart_id
from django.core.exceptions import ObjectDoesNotExist
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from shop.models import Product
from coupon.models import Coupon  # Import Coupon model

from django.db import transaction  # Import transaction for atomic operations

@login_required(login_url='accounts:login')
def payment_method(request):
    return render(request, 'shop/orders/payment_method.html')


@login_required(login_url='accounts:login')
def checkout(request, total=0, total_price=0, quantity=0, cart_items=None):
    tax = 0.00
    handing = 0.00
    applied_coupon = None
    discount_amount = 0.00

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total_price += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        total = total_price + 10

    except ObjectDoesNotExist:
        pass  # just ignore

    tax = round(((2 * total_price)/100), 2)
    grand_total = total_price + tax
    handing = 15.00

    # Check if a coupon is applied via session
    coupon_code = request.session.get('coupon_code')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            if coupon.is_valid():
                # Calculate discount
                if coupon.discount_type == 'percentage':
                    discount_amount = (coupon.discount_value / 100) * grand_total
                    if coupon.max_discount:
                        discount_amount = min(discount_amount, float(coupon.max_discount))
                elif coupon.discount_type == 'fixed':
                    discount_amount = float(coupon.discount_value)
                grand_total -= discount_amount
                applied_coupon = coupon
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
            request.session['coupon_code'] = None

    total = float(grand_total) + handing

    context = {
        'total_price': total_price,
        'quantity': quantity,
        'cart_items': cart_items,
        'handing': handing,
        'vat': tax,
        'order_total': total,
        'applied_coupon': applied_coupon,
        'discount_amount': discount_amount,
    }
    return render(request, 'shop/orders/checkout/checkout.html', context)


@login_required(login_url='accounts:login')
def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            if not coupon.is_valid():
                messages.error(request, 'This coupon is not valid or has expired.')
                return redirect('orders:checkout')

            cart = None
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
                if cart_items.exists():
                    print("cart_exists", cart_items.first())
                    cart = cart_items.first().cart
            else:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            print(cart,"cart")
            if cart:
                # Check minimum amount
                cart_total = sum(item.sub_total() for item in cart_items)
                if cart_total < coupon.min_amount:
                    messages.error(request, f'This coupon requires a minimum cart amount of {coupon.min_amount}.')
                    return redirect('orders:checkout')

                # If coupon is user-specific, verify user
                if coupon.user and coupon.user != request.user:
                    messages.error(request, 'You are not authorized to use this coupon.')
                    return redirect('orders:checkout')

                # Apply the coupon
                request.session['coupon_code'] = coupon.code
                messages.success(request, 'Coupon applied successfully!')
            else:
                messages.error(request, 'Your cart is empty.')

        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')

    return redirect('orders:checkout')


@login_required(login_url='accounts:login')
def remove_coupon(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
        messages.success(request, 'Coupon removed successfully!')
    return redirect('orders:checkout')


@login_required(login_url='accounts:login')
def payment(request, total=0, quantity=0):
    current_user = request.user
    handing = 15.0
    # if the cart count less than 0, redirect to shop page
    cart_items = CartItem.objects.filter(user=current_user, is_active=True)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('shop:shop')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = round(((2 * total)/100), 2)

    grand_total = total + tax
    handing = 15.00

    # Apply discount if coupon is applied
    discount_amount = 0.00
    coupon = None
    coupon_code = request.session.get('coupon_code')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            if coupon.is_valid():
                if coupon.discount_type == 'percentage':
                    discount_amount = (coupon.discount_value / 100) * grand_total
                    if coupon.max_discount:
                        discount_amount = min(discount_amount, float(coupon.max_discount))
                elif coupon.discount_type == 'fixed':
                    discount_amount = float(coupon.discount_value)
                grand_total -= discount_amount
            else:
                messages.error(request, 'This coupon is not valid or has expired.')
                del request.session['coupon_code']
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
            del request.session['coupon_code']

    total = float(grand_total) + handing

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # shop all the billing information inside Order table
                data = Order()
                data.user = current_user
                data.first_name = form.cleaned_data['first_name']
                data.last_name = form.cleaned_data['last_name']
                data.phone = form.cleaned_data['phone']
                data.email = form.cleaned_data['email']
                data.address = form.cleaned_data['address']
                data.country = form.cleaned_data['country']
                data.state = form.cleaned_data['state']
                data.city = form.cleaned_data['city']
                data.order_note = form.cleaned_data['order_note']
                data.order_total = total
                data.tax = tax
                data.discount = discount_amount  # Set discount
                if coupon and coupon.is_valid():
                    data.coupon = coupon  # Link coupon to order
                data.ip = request.META.get('REMOTE_ADDR')
                data.save()
                # Generate order number
                yr = int(datetime.date.today().strftime('%Y'))
                dt = int(datetime.date.today().strftime('%d'))
                mt = int(datetime.date.today().strftime('%m'))
                d = datetime.date(yr, mt, dt)
                current_date = d.strftime("%Y%m%d")  # e.g., 20210305
                order_number = current_date + str(data.id)
                data.order_number = order_number
                data.save()

                order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
                context = {
                    'order': order,
                    'cart_items': cart_items,
                    'handing': handing,
                    'vat': tax,
                    'order_total': total,
                    'discount_amount': discount_amount,
                }
                return render(request, 'shop/orders/checkout/payment.html', context)
        else:
            messages.error(request, 'Your information is not valid.')
            return redirect('orders:checkout')

    else:
        return redirect('shop:shop')


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside payment model 
    payment = Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        status=body['status'],
        amount_paid=order.order_total,
    )

    payment.save()

    order.payment = payment
    order.is_ordered = True
    if order.coupon:
        order.coupon.increment_usage()  # Increment coupon usage
    order.save()

    # Move the cart items to OrderProduct table 
    cart_items = CartItem.objects.filter(user=request.user, is_active=True)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # Add variation to OrderProduct table
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variation.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()

        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear Cart 
    CartItem.objects.filter(user=request.user, is_active=True).delete()

    # Remove coupon from session after successful payment
    if 'coupon_code' in request.session:
        del request.session['coupon_code']

    # Send order received email to customer 
    # Uncomment and customize the email templates as needed
    # subject = 'Thank you for your order!'
    # message = render_to_string('shop/orders/checkout/payment_received_email.html', {
    #     'user': request.user,
    #     'order': order,
    # })
    # to_email = request.user.email
    # send_email = EmailMessage(subject, message, to=[to_email])
    # send_email.send()

    # Send order received email to admin account 
    # subject = 'New Order Received'
    # message = render_to_string('shop/orders/checkout/admin_payment_received_email.html', {
    #     'user': request.user,
    #     'order': order,
    # })
    # to_email = ['admin@example.com']  # Replace with your admin email
    # send_email = EmailMessage(subject, message, to=to_email)
    # send_email.send()

    # Send order number and transaction id back to frontend via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)


def order_completed(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotall = 0
        for i in ordered_products:
            subtotall += i.product_price * i.quantity
        subtotal = round(subtotall, 2)
        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'shop/orders/order_completed/order_completed.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('shop:shop')
