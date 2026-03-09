from django.urls import path
from . import views

urlpatterns = [
    # Main Pages
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Cart Functions
    path('cart/', views.cart, name='cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_cart/<int:product_id>/<int:cart_item_id>/', views.remove_cart, name='remove_cart'),
    path('remove_cart_item/<int:product_id>/<int:cart_item_id>/', views.remove_cart_item, name='remove_cart_item'),
    
    # Checkout & Payment
    path('checkout/', views.checkout, name='checkout'),
    path('place_order/', views.place_order, name='place_order'),
    path('payment_success/', views.payment_success, name='payment_success'),
    
    # User Profile/Orders
    path('my_orders/', views.my_orders, name='my_orders'),
]