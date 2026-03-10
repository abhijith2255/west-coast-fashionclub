from django.contrib import admin
from .models import Category, Size, Color, Product, ProductVariant, ProductGallery, Cart, CartItem, Order, OrderItem, ReviewRating

# 1. Category Admin
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug')

# 2. Product Gallery Inline (ഇവിടെയാണ് ഓരോ കളറിനുമുള്ള ഫോട്ടോകൾ ആഡ് ചെയ്യുന്നത്)
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

# 3. Product Variant Inline (ഇവിടെയാണ് കളർ, സൈസ്, സ്റ്റോക്ക് എന്നിവ ആഡ് ചെയ്യുന്നത്)
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

# 4. Product Admin (പ്രധാന പ്രൊഡക്റ്റ് പേജ്)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'gender', 'is_active', 'modified_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('category', 'gender', 'is_active')
    search_fields = ('name', 'description')
    
    # പ്രൊഡക്റ്റ് ആഡ് ചെയ്യുന്ന പേജിൽ തന്നെ ഗാലറിയും വേരിയൻ്റുകളും കാണിക്കാൻ
    inlines = [ProductGalleryInline, ProductVariantInline]

# 5. Cart Admin
class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'date_added')

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'size', 'color', 'is_active')

# 6. Order Admin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'full_name', 'email', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('order_id', 'full_name', 'email', 'phone')
    list_per_page = 20

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'size', 'color')

# 7. Review Rating Admin
class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'rating', 'status', 'created_at')
    list_filter = ('status', 'rating')
    search_fields = ('product__name', 'name', 'review_text')


# --- Registering Models ---
admin.site.register(Category, CategoryAdmin)
admin.site.register(Size)
admin.site.register(Color)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant)
admin.site.register(ProductGallery)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(ReviewRating, ReviewRatingAdmin)