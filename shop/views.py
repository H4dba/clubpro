from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from decimal import Decimal

from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem
)


def product_list(request):
    """List all products with filtering"""
    products = Product.objects.filter(is_active=True)
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Featured products
    featured = request.GET.get('featured')
    if featured:
        products = products.filter(is_featured=True)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
    }
    
    return render(request, 'shop/product_list.html', context)


def product_detail(request, slug):
    """Product detail page"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get member price if user is logged in
    member_price = None
    if request.user.is_authenticated:
        member_price = product.get_price_for_user(request.user)
    
    # Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'member_price': member_price,
        'related_products': related_products,
    }
    
    return render(request, 'shop/product_detail.html', context)


def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user=None
        )
    return cart


@require_POST
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        messages.error(request, 'Quantidade inválida')
        return redirect('shop:product_detail', slug=product.slug)
    
    if product.stock < quantity:
        messages.error(request, 'Estoque insuficiente')
        return redirect('shop:product_detail', slug=product.slug)
    
    cart = get_or_create_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'{product.name} adicionado ao carrinho!')
    return redirect('shop:cart')


def cart_view(request):
    """View shopping cart"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    
    return render(request, 'shop/cart.html', context)


@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Verify cart belongs to user
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            messages.error(request, 'Acesso negado')
            return redirect('shop:cart')
    else:
        if cart_item.cart.session_key != request.session.session_key:
            messages.error(request, 'Acesso negado')
            return redirect('shop:cart')
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        cart_item.delete()
        messages.success(request, 'Item removido do carrinho')
    else:
        if cart_item.product.stock < quantity:
            messages.error(request, 'Estoque insuficiente')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Carrinho atualizado')
    
    return redirect('shop:cart')


@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Verify cart belongs to user
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            messages.error(request, 'Acesso negado')
            return redirect('shop:cart')
    else:
        if cart_item.cart.session_key != request.session.session_key:
            messages.error(request, 'Acesso negado')
            return redirect('shop:cart')
    
    cart_item.delete()
    messages.success(request, 'Item removido do carrinho')
    return redirect('shop:cart')


@login_required
def checkout(request):
    """Checkout process"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    if not cart_items.exists():
        messages.error(request, 'Seu carrinho está vazio')
        return redirect('shop:cart')
    
    # Check stock
    for item in cart_items:
        if item.product.stock < item.quantity:
            messages.error(request, f'{item.product.name} está fora de estoque')
            return redirect('shop:cart')
    
    if request.method == 'POST':
        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=request.POST.get('customer_name'),
            customer_email=request.POST.get('customer_email'),
            customer_phone=request.POST.get('customer_phone'),
            shipping_address=request.POST.get('shipping_address'),
            shipping_city=request.POST.get('shipping_city'),
            shipping_state=request.POST.get('shipping_state'),
            shipping_zip=request.POST.get('shipping_zip'),
            payment_method=request.POST.get('payment_method'),
            subtotal=cart.get_total(),
            total=cart.get_total(),
            notes=request.POST.get('notes', ''),
        )
        
        # Create order items
        for item in cart_items:
            price = item.product.get_price_for_user(request.user)
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=price,
                total=price * item.quantity
            )
        
        # Clear cart
        cart.items.all().delete()
        
        messages.success(request, f'Pedido {order.order_number} criado com sucesso!')
        return redirect('shop:order_detail', order_number=order.order_number)
    
    # Get member info if logged in
    member_info = {}
    if request.user.is_authenticated:
        try:
            from socios.models import Socio
            socio = Socio.objects.get(usuario=request.user)
            member_info = {
                'name': socio.nome_completo,
                'email': socio.email,
                'phone': socio.telefone or socio.celular,
                'address': socio.endereco_completo,
            }
        except:
            member_info = {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            }
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'member_info': member_info,
    }
    
    return render(request, 'shop/checkout.html', context)


@login_required
def order_detail(request, order_number):
    """Order detail page"""
    if request.user.is_superuser or request.user.is_staff:
        order = get_object_or_404(Order, order_number=order_number)
    else:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'shop/order_detail.html', context)


@login_required
def order_list(request):
    """User's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'shop/order_list.html', context)
