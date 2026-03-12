from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('add-product/', views.add_product, name='add_product'),
    path('products/', views.product_list, name='product_list'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('orders/', views.order_list, name='order_list'),
    path('update-order/<int:order_id>/', views.update_order_status, name='update_order_status'),
]