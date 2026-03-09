from django.db import models
from django.urls import reverse
from django.db.models import Avg

# 1. Category Model
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

# 2. Size & Color Models
class Size(models.Model):
    name = models.CharField(max_length=20, unique=True) # ഉദാ: S, M, L, XL

    def __str__(self):
        return self.name

class Color(models.Model):
    name = models.CharField(max_length=20, unique=True) # ഉദാ: Black, Red
    hex_code = models.CharField(max_length=10, blank=True) # ഉദാ: #000000

    def __str__(self):
        return self.name

# 3. Product Model
class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(max_length=1000, blank=True)
    price = models.IntegerField()
    discount_price = models.IntegerField(blank=True, null=True)
    main_image = models.ImageField(upload_to='photos/products')
    manual_review_count = models.IntegerField(default=0, help_text="ഉദാഹരണത്തിന് 155 എന്ന് നൽകിയാൽ 155 റിവ്യൂസ് എന്ന് കാണിക്കും")
    manual_avg_rating = models.FloatField(default=0.0, help_text="ഉദാഹരണത്തിന് 4.8 എന്ന് നൽകുക")
    
    stock = models.IntegerField()
    is_active = models.BooleanField(default=True)
    is_trending = models.BooleanField(default=False)
    
    sizes = models.ManyToManyField(Size, blank=True)
    colors = models.ManyToManyField(Color, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def get_url(self):
        return reverse('product_detail', args=[self.slug])

    def __str__(self):
        return self.name
    def get_review_count(self):
        if self.manual_review_count > 0:
            return self.manual_review_count
        return self.reviews.filter(status=True).count()

    def get_avg_rating(self):
        if self.manual_review_count > 0:
            return self.manual_avg_rating
        avg = self.reviews.filter(status=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg is not None else 0.0

# 4. Product Gallery (Multiple Images)
class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='photos/products/gallery')

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'

    def __str__(self):
        return self.product.name

# 5. Cart Models
class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    size = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        if self.product.discount_price:
            return self.product.discount_price * self.quantity
        return self.product.price * self.quantity

    def __str__(self):
        return self.product.name

# 6. Order & Order Item Models
class Order(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    total_amount = models.FloatField()
    payment_id = models.CharField(max_length=100, blank=True) # Razorpay Payment ID
    order_id = models.CharField(max_length=100, blank=True)   # Razorpay Order ID
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_id} - {self.full_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    size = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

# 7. Rating & Review Model
class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=100)
    rating = models.FloatField()
    review_text = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True) # അഡ്മിന് റിവ്യൂ ഹൈഡ് ചെയ്യാൻ

    def __str__(self):
        return f"{self.name} - {self.rating} Star"