from datetime import datetime
from time import timezone
from django.db import models
from django.db.models import UniqueConstraint

# from django.contrib.auth.models import User
from django.conf import settings
import pytz

from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(max_length=50, blank=True, null=True)  # Email riêng

    first_name = models.CharField(max_length=30, blank=True, null=True)  # First name
    last_name = models.CharField(max_length=30, blank=True, null=True)   # Last name
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Phone number
    address = models.CharField(max_length=255, blank=True, null=True)    # Address
    city = models.CharField(max_length=100, blank=True, null=True)       # City field
    zip = models.CharField(max_length=20, blank=True, null=True)         # ZIP code
    country = models.CharField(max_length=100, blank=True, null=True)    # Country
    date_of_birth = models.DateField(null=True, blank=True)              # Date of birth
    is_primary = models.BooleanField(default=False)                      # Default address checkbox

    def __str__(self):
        return self.user.username

class Category(models.Model):
    cate_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image_cat = models.CharField(max_length=200)
    detail = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.name
    
class Product(models.Model):
    pro_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Giá gốc
    stock = models.PositiveIntegerField(default=0)  # Số lượng tồn kho
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Mã SKU
    tags = models.CharField(max_length=200, null=True, blank=True)  # Các thẻ liên quan
    description = models.TextField(null=True, blank=True)  # Mô tả sản phẩm
    material = models.TextField(null=True, blank=True)  # Chất liệu
    storage_instruction = models.TextField(null=True, blank=True)  # Hướng dẫn bảo quản
    details = models.TextField(null=True, blank=True)  # Chi tiết sản phẩm
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    categories = models.TextField(null=True, blank=True)  # Các danh mục liên quan
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image_pro = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=True)  # Trạng thái sản phẩm

    def __str__(self):
        return self.title
    class Meta:
        db_table = 'home_product'

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'product'], name='unique_user_product_like')
        ]


class ProductSize(models.Model):
    SIZE_CHOICES = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, choices=SIZE_CHOICES)
    price = models.IntegerField()

    def __str__(self):
        return f"{self.product.title} - {self.get_size_display()} - {self.price} VND"
    
    class Meta:
        db_table = 'home_productsize'
        unique_together = ('product', 'size')

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.product.title} - {self.image}"
    class Meta:
        db_table = 'home_productimage'

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, choices=ProductSize.SIZE_CHOICES, default='S')
    quantity = models.PositiveIntegerField(default=1)
    sugar = models.CharField(max_length=10, choices=[('low', 'Ít'), ('normal', 'Bình thường'), ('high', 'Nhiều')], default='normal')
    tea = models.CharField(max_length=10, choices=[('low', 'Ít'), ('normal', 'Bình thường'), ('high', 'Nhiều')], default='normal')
    ice = models.CharField(max_length=10, choices=[('low', 'Ít'), ('normal', 'Bình thường'), ('high', 'Nhiều')], default='normal')

    def __str__(self):
        return f"{self.user.username} - {self.product.title} - {self.size}"
        
    class Meta:
        db_table = 'home_cartitem'
        unique_together = ('user', 'product', 'size') 

class Voucher(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiration_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        """Check if the voucher is valid."""
        if not self.is_active:
            return False
        # Đảm bảo rằng datetime.now() có múi giờ
        now = datetime.now(pytz.utc)  # Hoặc múi giờ tương ứng nếu cần
        if self.expiration_date and self.expiration_date < now:
            return False
        return True
    
    def __str__(self):
        return f"{self.code} - ${self.discount_amount}"


class HoaDon(models.Model):
    maHoaDon = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tongTien = models.DecimalField(max_digits=10, decimal_places=2)
    email = models.EmailField(max_length=50)
    diaChi = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ORDER_STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('processing', 'Đang chuẩn bị'),
        ('shipped', 'Đang giao hàng'),
        ('delivered', 'Đã giao hàng'),
        ('cancelled', 'Đã hủy'),
        ('failed', 'Thất bại')
    ]
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')

    PAYMENT_METHOD_CHOICES = [
        ('credit', 'Thẻ tín dụng/Ghi nợ'),
        ('paypal', 'Paypal'),
        ('cod', 'Thanh toán khi nhận hàng'),
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cod')

    voucher = models.ForeignKey(Voucher, null=True, blank=True, on_delete=models.SET_NULL)

    is_received = models.BooleanField(default=False)
    def get_shipping_steps(self):
        """Trả về số bước vận chuyển"""
        return self.events.count()

    def __str__(self):
        return f"#{self.maHoaDon} - {self.user.username} - {self.get_status_display()}"

    class Meta:
        db_table = 'home_hoadon'

class OrderEvent(models.Model):
    maEvent = models.AutoField(primary_key=True)
    order = models.ForeignKey(HoaDon, on_delete=models.CASCADE, related_name="events")
    time = models.DateTimeField(auto_now_add=True)  # Tự động lấy thời gian
    location = models.CharField(max_length=255, blank=True, null=True)  # Địa điểm giao hàng

    ORDER_STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('processing', 'Đang chuẩn bị'),
        ('shipped', 'Đang giao hàng'),
        ('delivered', 'Đã giao hàng'),
        ('cancelled', 'Đã hủy'),
        ('failed', 'Thất bại')
    ]
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'home_orderevent'
        ordering = ['time']

    def __str__(self):
        return f"Đơn hàng {self.order.maHoaDon} - {self.get_status_display()}"

# 📌 Cập nhật trạng thái hóa đơn khi có sự kiện mới
@receiver(post_save, sender=OrderEvent)
def update_order_status(sender, instance, **kwargs):
    instance.order.status = instance.status
    instance.order.save()


class Detail(models.Model):
    hoaDon = models.ForeignKey(HoaDon, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, choices=ProductSize.SIZE_CHOICES, default='S')    
    quantity = models.PositiveIntegerField(default=1)
    sugar = models.CharField(max_length=50, null=True, blank=True)  # Thông tin về đường
    ice = models.CharField(max_length=50, null=True, blank=True)  # Thông tin về đá
    tea = models.CharField(max_length=50, null=True, blank=True)  # Thông tin về ngọt


    def __str__(self):
        return f"{self.hoaDon} - {self.product.title} - Size: {self.size}"
    
    class Meta:
        db_table = 'home_detail'
        unique_together = ('hoaDon', 'product', 'size')

class Feedback(models.Model):
    mess_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(max_length=50)
    phone_number = models.IntegerField()
    message = models.TextField()
    time = models.DateTimeField(auto_now_add = True)
    def __str__(self):
        return f"{self.user.username} - {self.user.email}"
    
    class Meta:
        db_table = 'home_feedback'

class Review(models.Model):
    hoadon = models.ForeignKey(HoaDon, on_delete = models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    detail = models.ForeignKey(Detail, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Thêm liên kết với Product
    rate = models.IntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)
    # size = models.CharField(max_length=100, null=True, blank=True)  # Thêm trường size


    def __str__(self):
        return f"{self.user.username} - {self.product.title} - {self.created_at}"

    class Meta:
        db_table = 'home_review'

from django.db import models
from django.utils import timezone

class Policy(models.Model):
    POLICY_TYPES = [
        ('return', 'Chính sách đổi/trả'),
        ('delivery', 'Chính sách giao hàng'),
        ('payment', 'Chính sách thanh toán'),
        ('privacy', 'Chính sách bảo mật thông tin'),
        ('storage', 'Chính sách bảo quản thực phẩm'),
        ('promotion', 'Chính sách khuyến mãi'),
        ('cancel', 'Chính sách hủy đơn hàng'),
    ]

    type = models.CharField(max_length=20, choices=POLICY_TYPES, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class ShopInfo(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    open_time = models.TimeField()
    close_time = models.TimeField()
    website = models.URLField()
    is_open_weekend = models.BooleanField(default=True)
    ship_available = models.BooleanField(default=True)
    email = models.EmailField(max_length=50)
    zalo_link = models.URLField()
    facebook_link = models.URLField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.name