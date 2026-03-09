from django.contrib import admin
from .models import Category, Size, Color, Product, ProductGallery, Cart, CartItem, Order, OrderItem, ReviewRating

# 1. Category Admin
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug')

# 2. Product Gallery Inline
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

# 3. Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'manual_review_count', 'manual_avg_rating', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductGalleryInline]
    list_editable = ('price', 'stock', 'manual_review_count', 'manual_avg_rating', 'is_active') 
    list_filter = ('category', 'is_active', 'is_trending')
# 4. Order Item Inline
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'quantity', 'price', 'size', 'color')
    can_delete = False
    extra = 0

# 5. Order Admin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'full_name', 'email', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('order_id', 'full_name', 'email', 'phone')
    readonly_fields = ('order_id', 'payment_id', 'total_amount', 'created_at')
    inlines = [OrderItemInline] # ഓർഡർ ഡീറ്റൈൽസിൽ തന്നെ കസ്റ്റമർ എന്തൊക്കെ വാങ്ങി എന്ന് കാണാൻ

# 6. Review Admin
class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'rating', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'rating')

# 7. Cart Models (Usually for debugging only)
class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'date_added')

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'is_active')

# Registering Models
admin.site.register(Category, CategoryAdmin)
admin.site.register(Size)
admin.site.register(Color)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(ReviewRating, ReviewRatingAdmin)