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
    path('store/<str:gender>/', views.store, name='store_by_gender'),
    
    # Men-ൽ തന്നെ Shirts അല്ലെങ്കിൽ Shoes മാത്രം കാണിക്കാൻ
    path('store/<str:gender>/<slug:category_slug>/', views.store, name='store_by_gender_category'),
    path('store/', views.store, name='store'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register')
]
