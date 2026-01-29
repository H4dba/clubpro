"""
User-friendly admin views for shop management
Designed for non-technical business admins
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.views.decorators.http import require_POST
from decimal import Decimal

from .models import Product, Category, Order, OrderItem
from .forms import ProductForm, CategoryForm, OrderForm


def is_shop_admin(user):
    """Check if user can manage shop"""
    if not user.is_authenticated:
        return False
    # Superuser or staff can manage shop
    if user.is_superuser or user.is_staff:
        return True
    # You can also check for specific groups/permissions here
    return False


@login_required
@user_passes_test(is_shop_admin)
def shop_admin_dashboard(request):
    """Main dashboard for shop administration"""
    
    # Statistics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    # Low stock products
    low_stock_products = Product.objects.filter(
        is_active=True,
        stock__lt=10,
        stock__gt=0
    )[:5]
    
    # Out of stock products
    out_of_stock = Product.objects.filter(is_active=True, stock=0).count()
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
    }
    
    return render(request, 'shop/admin/dashboard.html', context)


@login_required
@user_passes_test(is_shop_admin)
def product_list_admin(request):
    """List all products with management options"""
    products = Product.objects.select_related('category').all()
    
    # Filters
    search = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(description__icontains=search)
        )
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    elif status_filter == 'out_of_stock':
        products = products.filter(stock=0)
    elif status_filter == 'low_stock':
        products = products.filter(stock__lt=10, stock__gt=0)
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'search': search,
        'category_filter': category_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'shop/admin/product_list.html', context)


@login_required
@user_passes_test(is_shop_admin)
def product_create(request):
    """Create a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Produto "{product.name}" criado com sucesso!')
            return redirect('shop:admin_product_list')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Criar Novo Produto',
    }
    
    return render(request, 'shop/admin/product_form.html', context)


@login_required
@user_passes_test(is_shop_admin)
def product_edit(request, product_id):
    """Edit an existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Produto "{product.name}" atualizado com sucesso!')
            return redirect('shop:admin_product_list')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': f'Editar Produto: {product.name}',
    }
    
    return render(request, 'shop/admin/product_form.html', context)


@login_required
@user_passes_test(is_shop_admin)
@require_POST
def product_toggle_active(request, product_id):
    """Toggle product active status"""
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save()
    
    status = 'ativado' if product.is_active else 'desativado'
    messages.success(request, f'Produto "{product.name}" {status} com sucesso!')
    
    return redirect('shop:admin_product_list')


@login_required
@user_passes_test(is_shop_admin)
def category_list_admin(request):
    """List all categories"""
    categories = Category.objects.annotate(
        product_count=Count('products')
    ).all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'shop/admin/category_list.html', context)


@login_required
@user_passes_test(is_shop_admin)
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoria "{category.name}" criada com sucesso!')
            return redirect('shop:admin_category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Criar Nova Categoria',
    }
    
    return render(request, 'shop/admin/category_form.html', context)


@login_required
@user_passes_test(is_shop_admin)
def category_edit(request, category_id):
    """Edit an existing category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoria "{category.name}" atualizada com sucesso!')
            return redirect('shop:admin_category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': f'Editar Categoria: {category.name}',
    }
    
    return render(request, 'shop/admin/category_form.html', context)


@login_required
@user_passes_test(is_shop_admin)
def order_list_admin(request):
    """List all orders"""
    orders = Order.objects.select_related('user').prefetch_related('items').all()
    
    # Filters
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment_status', '')
    search = request.GET.get('search', '')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search': search,
    }
    
    return render(request, 'shop/admin/order_list.html', context)


@login_required
@user_passes_test(is_shop_admin)
def order_detail_admin(request, order_number):
    """View order details"""
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save()
            messages.success(request, f'Pedido {order.order_number} atualizado com sucesso!')
            return redirect('shop:admin_order_list')
    else:
        form = OrderForm(instance=order)
    
    context = {
        'order': order,
        'form': form,
    }
    
    return render(request, 'shop/admin/order_detail.html', context)
