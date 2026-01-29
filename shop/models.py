from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import uuid


class Category(models.Model):
    """Product categories"""
    name = models.CharField(max_length=100, verbose_name="Nome")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Descrição")
    image = models.ImageField(
        upload_to='shop/categories/',
        blank=True,
        verbose_name="Imagem"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    """Products for sale"""
    name = models.CharField(max_length=200, verbose_name="Nome")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Descrição")
    short_description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descrição Curta"
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Preço"
    )
    member_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Desconto para Sócios (%)"
    )
    
    # Inventory
    stock = models.IntegerField(default=0, verbose_name="Estoque")
    sku = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="SKU"
    )
    
    # Relations
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        verbose_name="Categoria"
    )
    
    # Images
    main_image = models.ImageField(
        upload_to='shop/products/',
        blank=True,
        null=True,
        verbose_name="Imagem Principal"
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    is_featured = models.BooleanField(default=False, verbose_name="Destaque")
    
    # SEO
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Meta Título"
    )
    meta_description = models.TextField(
        blank=True,
        verbose_name="Meta Descrição"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"PROD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.slug})

    def get_price_for_user(self, user=None):
        """Get price with member discount if applicable"""
        price = self.price
        if user and user.is_authenticated:
            # Check if user is a member (socio)
            try:
                from socios.models import Socio
                socio = Socio.objects.get(usuario=user, status='ativo')
                if self.member_discount_percent > 0:
                    discount = price * (self.member_discount_percent / 100)
                    price = price - discount
            except:
                pass
        return price

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def member_price(self):
        """Calculate member price"""
        if self.member_discount_percent > 0:
            discount = self.price * (self.member_discount_percent / 100)
            return self.price - discount
        return self.price


class ProductImage(models.Model):
    """Additional product images"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='shop/products/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class Cart(models.Model):
    """Shopping cart"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrinho"
        verbose_name_plural = "Carrinhos"

    def __str__(self):
        if self.user:
            return f"Cart - {self.user.username}"
        return f"Cart - {self.session_key}"

    def get_total(self):
        """Calculate cart total"""
        return sum(item.get_total() for item in self.items.all())

    def get_item_count(self):
        """Get total number of items"""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Items in shopping cart"""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item do Carrinho"
        verbose_name_plural = "Itens do Carrinho"
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def get_total(self):
        """Calculate item total"""
        user = self.cart.user if self.cart.user else None
        price = self.product.get_price_for_user(user)
        return price * self.quantity


class Order(models.Model):
    """Customer orders"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('failed', 'Falhou'),
        ('refunded', 'Reembolsado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
        ('bank_transfer', 'Transferência Bancária'),
    ]

    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número do Pedido"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Customer info (for guest checkout)
    customer_name = models.CharField(max_length=200, verbose_name="Nome")
    customer_email = models.EmailField(verbose_name="E-mail")
    customer_phone = models.CharField(max_length=20, verbose_name="Telefone")
    
    # Shipping address
    shipping_address = models.TextField(verbose_name="Endereço de Entrega")
    shipping_city = models.CharField(max_length=100, verbose_name="Cidade")
    shipping_state = models.CharField(max_length=2, verbose_name="Estado")
    shipping_zip = models.CharField(max_length=10, verbose_name="CEP")
    
    # Order details
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Subtotal"
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Desconto"
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Status do Pagamento"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name="Método de Pagamento"
    )
    
    # Payment info
    payment_id = models.CharField(max_length=200, blank=True)
    pix_qr_code = models.TextField(blank=True)
    pix_code = models.CharField(max_length=200, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, verbose_name="Observações")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:order_detail', kwargs={'order_number': self.order_number})


class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
