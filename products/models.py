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

# 2. Size & Color Models (പുതിയ സൈസുകൾ ആഡ് ചെയ്യാൻ ഇത് സഹായിക്കും)
class Size(models.Model):
    name = models.CharField(max_length=20, unique=True) # ഉദാ: S, M, L, XL, XXL
    def __str__(self):
        return self.name

class Color(models.Model):
    name = models.CharField(max_length=20, unique=True) # ഉദാ: Black, White
    hex_code = models.CharField(max_length=10, blank=True)
    def __str__(self):
        return self.name

# 3. Product Model
GENDER_CHOICES = (
    ('Men', 'Men'),
    ('Women', 'Women'),
    ('Unisex', 'Unisex'),
)

class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='Men')
    
    description = models.TextField(max_length=1000, blank=True)
    price = models.IntegerField()
    discount_price = models.IntegerField(blank=True, null=True)
    
    # ഇത് പ്രൊഡക്റ്റിന്റെ മെയിൻ കവർ ഫോട്ടോ
    main_image = models.ImageField(upload_to='photos/products')
    
    manual_review_count = models.IntegerField(default=0)
    manual_avg_rating = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    is_trending = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def get_url(self):
        return reverse('product_detail', args=[self.slug])

    def __str__(self):
        return self.name

    def get_review_count(self):
        if self.manual_review_count > 0: return self.manual_review_count
        return self.reviews.filter(status=True).count()

    def get_avg_rating(self):
        if self.manual_review_count > 0: return self.manual_avg_rating
        avg = self.reviews.filter(status=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg is not None else 0.0

# 4. Product Variant Model (ഇവിടെയാണ് ഓരോ കളറിനും സൈസിനുമുള്ള സ്റ്റോക്ക് വരുന്നത്)
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/variant_images/', blank=True, null=True)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('product', 'color', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"

# 5. Product Gallery (ഇവിടെ ഫോട്ടോകൾക്ക് കളർ കൊടുക്കാം!)
class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True, help_text="ഈ ഫോട്ടോ ഏത് കളർ ഷർട്ടിന്റേതാണെന്ന് സെലക്ട് ചെയ്യുക")
    image = models.ImageField(upload_to='photos/products/gallery')

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'

    def __str__(self):
        return f"{self.product.name} Image"

# 6. Cart Models
class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)
    def __str__(self): return self.cart_id

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    size = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        if self.product.discount_price: return self.product.discount_price * self.quantity
        return self.product.price * self.quantity

# 7. Order & Order Item Models
class Order(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    total_amount = models.FloatField()
    payment_id = models.CharField(max_length=100, blank=True)
    order_id = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Order #{self.order_id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    size = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)

# 8. Review Rating Model
class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=100)
    rating = models.FloatField()
    review_text = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)