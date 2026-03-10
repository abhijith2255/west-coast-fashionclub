import json
import razorpay
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg
from django.conf import settings
from .models import Color, Product, Cart, CartItem, Order, OrderItem, ReviewRating, Category, ProductVariant, ProductGallery, Size

# 1. Home Page
def home(request):
    trending_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    context = {'products': trending_products}
    return render(request, 'home.html', context)

# 2. Product Detail Page
# 2. Product Detail Page
# 2. Product Detail Page
# 2. Product Detail Page
def product_detail(request, slug):
    try:
        product = Product.objects.get(slug=slug)
        product_gallery = ProductGallery.objects.filter(product=product)
        
        variants = ProductVariant.objects.filter(product=product, is_active=True)
        sizes = variants.values_list('size__name', flat=True).distinct()
        
        reviews = ReviewRating.objects.filter(product=product, status=True)
        review_count = reviews.count()
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        
        variant_data = {}
        color_images = {}
        color_data = []
        added_colors = set()

        for v in variants:
            key = f"{v.color.name}_{v.size.name}"
            variant_data[key] = v.stock
            
            img_url = v.image.url if hasattr(v, 'image') and v.image else product.main_image.url
            color_images[v.color.name] = img_url

            if v.color.name not in added_colors:
                color_data.append({'name': v.color.name, 'url': img_url})
                added_colors.add(v.color.name)

        # 🌟 ഗാലറി ഫോട്ടോകളെ കളർ തിരിച്ച് ഗ്രൂപ്പ് ചെയ്യാനുള്ള പുതിയ കോഡ് 🌟
        color_gallery_data = {}
        for img in product_gallery:
            if img.color: # ഫോട്ടോയ്ക്ക് കളർ കൊടുത്തിട്ടുണ്ടെങ്കിൽ
                c_name = img.color.name
                if c_name not in color_gallery_data:
                    color_gallery_data[c_name] = []
                color_gallery_data[c_name].append(img.image.url)
            
    except Exception as e:
        raise e

    context = {
        'product': product,
        'product_gallery': product_gallery,
        'sizes': sizes,
        'color_data': color_data,
        'variant_data': json.dumps(variant_data),
        'color_images': json.dumps(color_images),
        'color_gallery': json.dumps(color_gallery_data), # 🌟 പുതിയ ഡാറ്റ 🌟
        'review_count': review_count,
        'average_rating': average_rating,
    }
    return render(request, 'product_detail.html', context)

# 3. Private function to get/create main Cart ID
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return request.session.session_key

# 4. Add to Cart & Buy Now Logic (Flipkart Style)
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        size_name = request.POST.get('size')
        color_name = request.POST.get('color')
        action = request.POST.get('action') # ഏത് ബട്ടൺ ആണ് ക്ലിക്ക് ചെയ്തതെന്ന് മനസ്സിലാക്കാൻ

        if not size_name or not color_name:
            return redirect(product.get_url())

        try:
            color_obj = Color.objects.get(name=color_name)
            size_obj = Size.objects.get(name=size_name)
            variant = ProductVariant.objects.get(product=product, color=color_obj, size=size_obj)
            
            if variant.stock <= 0:
                return redirect(product.get_url())
        except (Color.DoesNotExist, Size.DoesNotExist, ProductVariant.DoesNotExist):
            return redirect(product.get_url())

        # 🌟 പ്രധാന മാറ്റം: Order Now ആണെങ്കിൽ ഒരു താൽക്കാലിക കാർട്ട് ഉണ്ടാക്കുന്നു 🌟
        if action == 'buy_now':
            target_cart_id = _cart_id(request) + "-buynow"
            request.session['active_checkout'] = 'buy_now' # ചെക്ക്ഔട്ട് പേജിന് മനസ്സിലാകാൻ
        else:
            target_cart_id = _cart_id(request)
            request.session['active_checkout'] = 'cart'

        try:
            cart = Cart.objects.get(cart_id=target_cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=target_cart_id)
            cart.save()

        # Buy Now ആണെങ്കിൽ ആ കാർട്ടിലെ പഴയ സാധനം മാത്രം മാറ്റുന്നു (മെയിൻ കാർട്ടിനെ ബാധിക്കില്ല)
        if action == 'buy_now':
            CartItem.objects.filter(cart=cart).delete()

        item_exists = CartItem.objects.filter(product=product, cart=cart, size=size_name, color=color_name).exists()

        if item_exists:
            cart_item = CartItem.objects.get(product=product, cart=cart, size=size_name, color=color_name)
            if cart_item.quantity < variant.stock:
                cart_item.quantity += 1
                cart_item.save()
        else:
            CartItem.objects.create(product=product, cart=cart, quantity=1, size=size_name, color=color_name)

        if action == 'buy_now':
            return redirect('checkout')
        else:
            return redirect('cart')

    return redirect('home')

# 5. Cart Page View
def cart(request):
    # കസ്റ്റമർ കാർട്ട് പേജിലേക്ക് വന്നാൽ അത് മെയിൻ കാർട്ട് ആക്കി സെറ്റ് ചെയ്യുന്നു
    request.session['active_checkout'] = 'cart' 
    
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

# 6. Decrease Quantity
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

# 7. Delete Item
def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart')

# 8. Checkout Page View
def checkout(request):
    total = 0
    cart_items = []
    
    # 🌟 ഏതെങ്കിലും ഒരു ഐറ്റം മാത്രമാണോ അതോ മെയിൻ കാർട്ട് ആണോ എന്ന് പരിശോധിക്കുന്നു 🌟
    target_cart_id = _cart_id(request) + "-buynow" if request.session.get('active_checkout') == 'buy_now' else _cart_id(request)
    
    try:
        cart = Cart.objects.get(cart_id=target_cart_id)
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
def place_order(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')

        if not all([full_name, email, phone, address, city, pincode]):
            return redirect('checkout')

        request.session['customer_email'] = email 

        target_cart_id = _cart_id(request) + "-buynow" if request.session.get('active_checkout') == 'buy_now' else _cart_id(request)

        try:
            cart = Cart.objects.get(cart_id=target_cart_id)
            cart_items = CartItem.objects.filter(cart=cart)
            if not cart_items.exists():
                return redirect('home') 
        except Cart.DoesNotExist:
            return redirect('home')

        total = sum(item.sub_total() for item in cart_items)
        amount = int(total * 100) 

        order = Order.objects.create(
            full_name=full_name, email=email, phone=phone,
            address=address, city=city, pincode=pincode,
            total_amount=total
        )

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
            'razorpay_key': "rzp_live_SP8AhpYHRBju0D",
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

        # ഓർഡർ പൂർത്തിയായ കാർട്ട് മാത്രം ക്ലിയർ ചെയ്യുന്നു (മെയിൻ കാർട്ട് അല്ലെങ്കിൽ ബൈ നൗ കാർട്ട്)
        target_cart_id = _cart_id(request) + "-buynow" if request.session.get('active_checkout') == 'buy_now' else _cart_id(request)
        cart = Cart.objects.get(cart_id=target_cart_id)
        CartItem.objects.filter(cart=cart).delete()
        
        # പർച്ചേസ് കഴിഞ്ഞാൽ തിരിച്ച് മെയിൻ കാർട്ടിലേക്ക് തന്നെ സെറ്റ് ചെയ്യുന്നു
        request.session['active_checkout'] = 'cart'

    except (Order.DoesNotExist, Cart.DoesNotExist):
        return redirect('home')

    context = {
        'payment_id': payment_id,
        'order_id': order.order_id, # order.id-ന് പകരം order_id ആയിരിക്കും നല്ലത്
    }
    return render(request, 'payment_success.html', context)

# 11. My Orders
def my_orders(request):
    email = request.session.get('customer_email')
    orders = Order.objects.filter(email=email, is_paid=True).order_by('-created_at') if email else None
    context = {'orders': orders}
    return render(request, 'my_order.html', context)

# 12. Store Page
def store(request, gender=None, category_slug=None):
    products = Product.objects.filter(is_active=True)
    if gender:
        products = products.filter(gender=gender.capitalize())
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    context = {
        'products': products,
        'product_count': products.count(),
        'current_gender': gender,
    }
    return render(request, 'store.html', context)