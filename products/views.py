from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg
from .models import Product, Cart, CartItem, Order, OrderItem,ReviewRating
import razorpay

# 1. Home Page
def home(request):
    # ട്രെൻഡിങ് ആയ പ്രോഡക്റ്റുകൾ മാത്രം എടുക്കാൻ
    trending_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    context = {'products': trending_products}
    return render(request, 'home.html', context)


# 2. Product Detail & Reviews
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # യഥാർത്ഥ റിവ്യൂകൾ എടുക്കുന്നു (ഏറ്റവും പുതിയ 10 എണ്ണം മാത്രം കാണിച്ചാൽ മതി, പേജ് സ്ലോ ആവില്ല)
    reviews = ReviewRating.objects.filter(product=product, status=True).order_by('-created_at')[:10]
    
    # അഡ്മിൻ പാനലിൽ നിങ്ങൾ മാന്വലായി നമ്പർ (ഉദാ: 155) നൽകിയിട്ടുണ്ടെങ്കിൽ അത് ഉപയോഗിക്കുക
    if product.manual_review_count > 0:
        review_count = product.manual_review_count
        avg_rating = product.manual_avg_rating
    else:
        # മാന്വലായി നൽകിയിട്ടില്ലെങ്കിൽ യഥാർത്ഥ കൗണ്ട് എടുക്കുക
        real_reviews = ReviewRating.objects.filter(product=product, status=True)
        review_count = real_reviews.count()
        avg = real_reviews.aggregate(Avg('rating'))['rating__avg']
        avg_rating = round(avg, 1) if avg is not None else 0

    context = {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': review_count,
    }
    return render(request, 'product_detail.html', context)


# 3. Private function to get/create Cart ID
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return request.session.session_key


# 4. Add to Cart
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        size = request.POST.get('size')
        color = request.POST.get('color')

        if not size or not color:
            return redirect('product_detail', slug=product.slug)

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()

        item_exists = CartItem.objects.filter(product=product, cart=cart, size=size, color=color).exists()

        if item_exists:
            item = CartItem.objects.get(product=product, cart=cart, size=size, color=color)
            item.quantity += 1
            item.save()
        else:
            CartItem.objects.create(product=product, cart=cart, quantity=1, size=size, color=color)

        return redirect('cart')
    return redirect('home')


# 5. Cart Page
def cart(request):
    total = 0
    cart_items = []
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += cart_item.sub_total()
    except Cart.DoesNotExist:
        pass

    context = {'total': total, 'cart_items': cart_items}
    return render(request, 'cart.html', context)


# 6. Decrease Cart Item Quantity
def remove_cart(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart')


# 7. Delete Cart Item Completely
def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


# 8. Checkout Page
def checkout(request):
    total = 0
    cart_items = []
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        if not cart_items:
            return redirect('home')
        for cart_item in cart_items:
            total += cart_item.sub_total()
    except Cart.DoesNotExist:
        return redirect('home')

    context = {'total': total, 'cart_items': cart_items}
    return render(request, 'checkout.html', context)


# 9. Place Order & Razorpay Integration
# 9. Place Order & Razorpay Integration
def place_order(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address1')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')

        request.session['customer_email'] = email 

        # Cart എടുക്കുമ്പോൾ Error വരാതിരിക്കാൻ try-except ചേർക്കുന്നു
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart)
            
            # കാർട്ടിൽ ഒന്നുമില്ലെങ്കിലും തിരികെ ഹോമിലേക്ക് പോകാൻ
            if not cart_items.exists():
                return redirect('home') 
                
        except Cart.DoesNotExist:
            return redirect('home') # Cart കണ്ടില്ലെങ്കിൽ ഹോമിലേക്ക് പോവുക

        total = sum(item.sub_total() for item in cart_items)
        amount = int(total * 100) # Razorpay requires amount in paise

        order = Order.objects.create(
            full_name=full_name, email=email, phone=phone,
            address=address, city=city, pincode=pincode,
            total_amount=total
        )

        # നിങ്ങളുടെ യഥാർത്ഥ കീകൾ ഇവിടെ ഉണ്ടെന്ന് ഉറപ്പുവരുത്തുക
        client = razorpay.Client(auth=("rzp_live_SP8AhpYHRBju0D", "ze7Ev5jrSYKiIBlk4l3tgnTM")) 
        payment = client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '1'
        })

        order.order_id = payment['id']
        order.save()

        for item in cart_items:
            OrderItem.objects.create(
                order=order, product=item.product, quantity=item.quantity,
                price=item.product.discount_price if item.product.discount_price else item.product.price, 
                size=item.size, color=item.color
            )

        context = {
            'order': order,
            'payment': payment,
            'razorpay_key': "rzp_live_SP8AhpYHRBju0D", # നിങ്ങളുടെ യഥാർത്ഥ Key ID ഇവിടെ നൽകുക
            'total': total
        }
        return render(request, 'payment.html', context)
    return redirect('cart')

# 10. Payment Success & Clear Cart
def payment_success(request):
    payment_id = request.GET.get('payment_id')
    order_id = request.GET.get('order_id')

    try:
        order = Order.objects.get(order_id=order_id)
        order.is_paid = True
        order.payment_id = payment_id
        order.save()

        # ഓർഡർ കൺഫേം ആയതുകൊണ്ട് കാർട്ട് ക്ലിയർ ചെയ്യുന്നു
        cart = Cart.objects.get(cart_id=_cart_id(request))
        CartItem.objects.filter(cart=cart).delete()

    except (Order.DoesNotExist, Cart.DoesNotExist):
        return redirect('home')

    context = {
        'payment_id': payment_id,
        'order_id': order.id,
    }
    return render(request, 'payment_success.html', context)


# 11. My Orders (Purchase History)
def my_orders(request):
    email = request.session.get('customer_email')
    
    if email:
        orders = Order.objects.filter(email=email, is_paid=True).order_by('-created_at')
    else:
        orders = None

    context = {'orders': orders}
    return render(request, 'my_order.html', context)