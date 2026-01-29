from django.urls import path
from . import views
from . import admin_views

app_name = 'shop'

urlpatterns = [
    # Public shop views
    path('', views.product_list, name='product_list'),
    path('produto/<slug:slug>/', views.product_detail, name='product_detail'),
    path('carrinho/', views.cart_view, name='cart'),
    path('carrinho/adicionar/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('carrinho/atualizar/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('carrinho/remover/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('pedidos/', views.order_list, name='order_list'),
    path('pedido/<str:order_number>/', views.order_detail, name='order_detail'),
    
    # Admin views
    path('admin/', admin_views.shop_admin_dashboard, name='admin_dashboard'),
    path('admin/produtos/', admin_views.product_list_admin, name='admin_product_list'),
    path('admin/produtos/criar/', admin_views.product_create, name='admin_product_create'),
    path('admin/produtos/<int:product_id>/editar/', admin_views.product_edit, name='admin_product_edit'),
    path('admin/produtos/<int:product_id>/toggle/', admin_views.product_toggle_active, name='admin_product_toggle'),
    path('admin/categorias/', admin_views.category_list_admin, name='admin_category_list'),
    path('admin/categorias/criar/', admin_views.category_create, name='admin_category_create'),
    path('admin/categorias/<int:category_id>/editar/', admin_views.category_edit, name='admin_category_edit'),
    path('admin/pedidos/', admin_views.order_list_admin, name='admin_order_list'),
    path('admin/pedidos/<str:order_number>/', admin_views.order_detail_admin, name='admin_order_detail'),
]
