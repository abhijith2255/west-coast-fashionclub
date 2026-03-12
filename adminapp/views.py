from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Sum

from products.models import Order, Product, Category, Color, Size, ProductVariant, ProductGallery

@staff_member_required
def dashboard(request):
    total_orders = Order.objects.filter(is_paid=True).count()
    total_sales = Order.objects.filter(is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_customers = Order.objects.values('email').distinct().count()
    
    recent_orders = Order.objects.filter(is_paid=True).order_by('-created_at')[:5]
    low_stock_products = ProductVariant.objects.filter(stock__lt=10, is_active=True)

    context = {
        'total_orders': total_orders, 'total_sales': total_sales,
        'total_customers': total_customers, 'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'bdm/admin_dashboard.html', context)

@staff_member_required
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/order_list.html', {'orders': orders})

@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        if hasattr(order, 'status'):
            order.status = status 
            order.save()
            messages.success(request, f'Order #{order.order_id} status updated to {status}')
        else:
            messages.error(request, 'Status field not found in Order model.')
    return redirect('order_list')

# 🌟 Add Product with Demo Reviews 🌟
@staff_member_required
def add_product(request):
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()
    
    if request.method == 'POST':
        # ഏത് ബട്ടൺ ആണ് അമർത്തിയത് എന്ന് നോക്കുന്നു
        action = request.POST.get('action')

        # 1. 🌟 പുതിയ കളർ സേവ് ചെയ്യാൻ 🌟
        if action == 'add_color':
            color_name = request.POST.get('color_name')
            if color_name:
                Color.objects.get_or_create(name=color_name)
                messages.success(request, f'Color "{color_name}" added!')
            return redirect('add_product')

        # 2. 🌟 പുതിയ സൈസ് സേവ് ചെയ്യാൻ 🌟
        elif action == 'add_size':
            size_name = request.POST.get('size_name')
            if size_name:
                Size.objects.get_or_create(name=size_name)
                messages.success(request, f'Size "{size_name}" added!')
            return redirect('add_product')

        # 3. 🌟 മെയിൻ പ്രൊഡക്റ്റ് സേവ് ചെയ്യാൻ 🌟
        elif action == 'add_product':
            name = request.POST.get('name')
            slug = slugify(name)
            description = request.POST.get('description')
            price = request.POST.get('price')
            discount_price = request.POST.get('discount_price') or None
            category_id = request.POST.get('category')
            gender = request.POST.get('gender')
            
            manual_review_count = request.POST.get('manual_review_count') or 0
            manual_avg_rating = request.POST.get('manual_avg_rating') or 0.0
            
            total_colors = int(request.POST.get('total_colors', 1))
            main_image = request.FILES.get('image_0') 
                
            try:
                category = Category.objects.get(id=category_id)
                product = Product.objects.create(
                    name=name, slug=slug, description=description,
                    price=price, discount_price=discount_price,
                    category=category, gender=gender,
                    main_image=main_image, is_active=True,
                    manual_review_count=manual_review_count,
                    manual_avg_rating=manual_avg_rating      
                )
                
                # വേരിയന്റുകൾ ലൂപ്പ് വഴി സേവ് ചെയ്യുന്നു
                for i in range(total_colors):
                    color_id = request.POST.get(f'color_{i}')
                    if not color_id: continue 

                    color = Color.objects.get(id=color_id)
                    variant_image = request.FILES.get(f'image_{i}')
                    
                    for size in sizes:
                        stock_val = request.POST.get(f'stock_{i}_{size.id}', '0')
                        if stock_val.isdigit() and int(stock_val) > 0:
                            ProductVariant.objects.create(
                                product=product, color=color, size=size,
                                stock=int(stock_val), image=variant_image
                            )
                    
                    # ഗാലറി ഇമേജുകൾ
                    gallery_images = request.FILES.getlist(f'gallery_{i}')
                    for img in gallery_images:
                        ProductGallery.objects.create(product=product, color=color, image=img)

                messages.success(request, f'Product "{name}" published successfully!')
                return redirect('admin_dashboard')
                
            except Exception as e:
                messages.error(request, f'Error: {e}')
            
    return render(request, 'bdm/add_product.html', {
        'categories': categories, 'colors': colors, 'sizes': sizes
    })

# 🌟 Product List View 🌟
@staff_member_required
def product_list(request):
    # എല്ലാ പ്രൊഡക്റ്റുകളും പുതിയത് ആദ്യം എന്ന രീതിയിൽ എടുക്കുന്നു
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'bdm/product_list.html', {'products': products})

# 🌟 Delete Product View 🌟
@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete() # ഇത് ഡാറ്റാബേസിൽ നിന്ന് പ്രൊഡക്റ്റ് ഡിലീറ്റ് ചെയ്യും
    messages.success(request, f'Product "{product_name}" has been deleted successfully!')
    return redirect('product_list')

# 🌟 Edit Product View 🌟
# 🌟 Edit Product View (Updated with Existing Variants) 🌟
@staff_member_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()
    
    # പഴയ കളറുകളും ഫോട്ടോകളും സ്റ്റോക്കും എടുക്കാനുള്ള ലോജിക്
    existing_variant_colors = product.variants.values_list('color', flat=True).distinct()
    existing_data = []
    
    for color_id in existing_variant_colors:
        color_obj = Color.objects.get(id=color_id)
        variant_obj = product.variants.filter(color=color_obj).first()
        variant_image = variant_obj.image if variant_obj else None
        
        stocks_list = []
        for size in sizes:
            v = product.variants.filter(color=color_obj, size=size).first()
            stocks_list.append({
                'size_id': size.id,
                'size_name': size.name,
                'stock': v.stock if v else 0
            })
            
        gallery_imgs = product.gallery_images.filter(color=color_obj)
        
        existing_data.append({
            'color': color_obj,
            'image': variant_image,
            'stocks': stocks_list,
            'gallery': gallery_imgs
        })
    
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_color':
            color_name = request.POST.get('color_name')
            if color_name:
                Color.objects.get_or_create(name=color_name)
                messages.success(request, f'Color "{color_name}" added!')
            return redirect('edit_product', product_id=product.id)

        elif action == 'add_size':
            size_name = request.POST.get('size_name')
            if size_name:
                Size.objects.get_or_create(name=size_name)
                messages.success(request, f'Size "{size_name}" added!')
            return redirect('edit_product', product_id=product.id)

        else:
            # 🌟 1. ഡിലീറ്റ് ചെയ്യാൻ സെലക്ട് ചെയ്ത ഗാലറി ഫോട്ടോകൾ ഡിലീറ്റ് ചെയ്യുന്നു 🌟
            for key in request.POST:
                if key.startswith('delete_gallery_'):
                    img_id = key.split('_')[-1]
                    ProductGallery.objects.filter(id=img_id).delete()

            # 2. മെയിൻ പ്രൊഡക്റ്റ് അപ്ഡേറ്റ്
            product.name = request.POST.get('name')
            product.slug = slugify(product.name)
            product.description = request.POST.get('description')
            product.price = request.POST.get('price')
            
            discount_price = request.POST.get('discount_price')
            product.discount_price = discount_price if discount_price else None
            
            category_id = request.POST.get('category')
            product.category = Category.objects.get(id=category_id)
            product.gender = request.POST.get('gender')
            
            manual_review_count = request.POST.get('manual_review_count')
            manual_avg_rating = request.POST.get('manual_avg_rating')
            product.manual_review_count = int(manual_review_count) if manual_review_count else 0
            product.manual_avg_rating = float(manual_avg_rating) if manual_avg_rating else 0.0

            if request.FILES.get('main_image'):
                product.main_image = request.FILES.get('main_image')

            product.save()

            # 3. പഴയ വേരിയന്റുകൾ (ഫോട്ടോ, സ്റ്റോക്ക്) അപ്ഡേറ്റ് ചെയ്യുന്നു
            for color_id in existing_variant_colors:
                color_obj = Color.objects.get(id=color_id)
                
                # വേരിയന്റ് മെയിൻ ഫോട്ടോ മാറ്റുന്നു (ഉണ്ടെങ്കിൽ)
                new_variant_image = request.FILES.get(f'existing_image_{color_id}')
                if new_variant_image:
                    variants_to_update = ProductVariant.objects.filter(product=product, color=color_obj)
                    for v in variants_to_update:
                        v.image = new_variant_image
                        v.save()
                
                # പുതിയ ഗാലറി ഫോട്ടോകൾ ചേർക്കുന്നു (ഉണ്ടെങ്കിൽ)
                new_gallery_images = request.FILES.getlist(f'existing_gallery_{color_id}')
                for img in new_gallery_images:
                    ProductGallery.objects.create(product=product, color=color_obj, image=img)

                # പഴയ സ്റ്റോക്കുകൾ അപ്ഡേറ്റ് ചെയ്യുന്നു
                for size in sizes:
                    stock_key = f'existing_stock_{color_id}_{size.id}'
                    if stock_key in request.POST:
                        new_stock = int(request.POST.get(stock_key, 0))
                        ProductVariant.objects.update_or_create(
                            product=product, color=color_obj, size=size,
                            defaults={'stock': new_stock}
                        )

            # 4. പുതിയ കളർ വേരിയന്റുകൾ ആഡ് ചെയ്തിട്ടുണ്ടെങ്കിൽ സേവ് ചെയ്യുന്നു
            total_colors = int(request.POST.get('total_colors', 0))
            for i in range(total_colors):
                color_id = request.POST.get(f'color_{i}')
                if not color_id: continue 

                color = Color.objects.get(id=color_id)
                variant_image = request.FILES.get(f'image_{i}')
                
                for size in sizes:
                    stock_val = request.POST.get(f'stock_{i}_{size.id}', '0')
                    if stock_val.isdigit() and int(stock_val) > 0:
                        ProductVariant.objects.create(
                            product=product, color=color, size=size,
                            stock=int(stock_val), image=variant_image
                        )
                
                gallery_images = request.FILES.getlist(f'gallery_{i}')
                for img in gallery_images:
                    ProductGallery.objects.create(product=product, color=color, image=img)

            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('edit_product', product_id=product.id)
        
    return render(request, 'bdm/edit_product.html', {
        'product': product, 'categories': categories, 'colors': colors, 'sizes': sizes,
        'existing_data': existing_data
    })

@staff_member_required
def order_list(request):
    # എല്ലാ ഓർഡറുകളും പുതിയത് ആദ്യം എന്ന രീതിയിൽ എടുക്കുന്നു
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/order_list.html', {'orders': orders})

# 🌟 2. Update Order Status View 🌟
@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        # ⚠️ ശ്രദ്ധിക്കുക: നിങ്ങളുടെ Order മോഡലിൽ 'status' എന്ന ഫീൽഡ് ഉണ്ടായിരിക്കണം. 
        # ഇല്ലെങ്കിൽ models.py ൽ അത് (ഉദാ: status = models.CharField(max_length=20, default='Pending')) ചേർക്കാൻ മറക്കരുത്.
        if hasattr(order, 'status'):
            order.status = status 
            order.save()
            messages.success(request, f'Order #{order.order_id} status updated to {status}')
        else:
            messages.error(request, "Status field is missing in your Order model! Please add it.")
            
    return redirect('order_list')