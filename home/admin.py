from django.contrib import admin
from home.models import (
    Policy, ShopInfo, UserProfile, Category, Product, ProductSize, ProductImage, 
    CartItem, HoaDon, OrderEvent, Detail, Feedback, Review, Voucher
)

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_amount', 'min_spend', 'expiration_date', 'is_active')
    list_filter = ('is_active', 'expiration_date')
    search_fields = ('code',)
    ordering = ('-expiration_date',)
# UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'phone_number', 'address', 'date_of_birth', 'is_primary')
    list_filter = ('is_primary', 'date_of_birth')
    search_fields = ('user__username', 'email', 'phone_number', 'address')
    ordering = ('user__username',)

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('cate_id', 'name', 'created_at', 'updated_at', 'image_cat', 'detail')
    search_fields = ('name',)
    ordering = ('-created_at',)

# ProductImage Inline
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image',)
    can_delete = True  # Cho phép xóa hình ảnh

# ProductSize Inline
class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ('size', 'price')
    can_delete = True  # Cho phép xóa kích thước
    verbose_name = "Product Size"
    verbose_name_plural = "Product Sizes"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Hiển thị tất cả các trường trừ 'pro_id' vì nó là AutoField
    list_display = [field.name for field in Product._meta.fields if field.name != 'pro_id']  
    list_filter = ('category', 'created_at', 'updated_at')  # Lọc theo các trường phù hợp
    search_fields = ('title', 'category__name')  # Tìm kiếm theo tiêu đề và danh mục
    ordering = ('-created_at',)  # Sắp xếp theo thời gian tạo mới nhất
    inlines = [ProductImageInline, ProductSizeInline]  # Thêm inline quản lý ảnh và kích thước
    fieldsets = (
        ('Product Details', {
            'fields': [field.name for field in Product._meta.fields if field.name not in ('created_at', 'updated_at', 'pro_id')],
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')  # Đặt các trường thời gian chỉ đọc

# ProductImage Admin
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'image')
    list_filter = ('product__category',)
    search_fields = ('product__title',)

# ProductSize Admin
@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'size', 'price')
    list_filter = ('size', 'product__category')
    search_fields = ('product__title', 'size')

# CartItem Admin
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'size', 'quantity')
    list_filter = ('size', 'product__category', 'user')
    search_fields = ('user__username', 'product__title')

# OrderEvent Admin
@admin.register(OrderEvent)
class OrderEventAdmin(admin.ModelAdmin):
    list_display = ('order', 'time', 'location', 'status')
    list_filter = ('status',)

    # search_fields = ('order__maHoaDon', 'location', 'event')

# Detail Admin
@admin.register(Detail)
class DetailAdmin(admin.ModelAdmin):
    list_display = ('hoaDon', 'product', 'size', 'quantity')
    list_filter = ('size', 'product__category')
    search_fields = ('hoaDon__maHoaDon', 'product__title', 'size')

# HoaDon Admin with OrderEvent and Detail Inline
class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 1
    fields = ('maEvent','time', 'location', 'event')
    verbose_name = "Shipping Event"
    verbose_name_plural = "Shipping Events"
    can_delete = True


class DetailInline(admin.TabularInline):
    model = Detail
    extra = 1
    fields = ('product', 'size', 'quantity')
    verbose_name = "Order Item"
    verbose_name_plural = "Order Items"
    can_delete = True



# @admin.register(HoaDon)
# class HoaDonAdmin(admin.ModelAdmin):
#     list_display = ('maHoaDon', 'user', 'tongTien', 'email', 'created_at', 'status', 'payment_method', 'is_received')
#     list_filter = ('status', 'payment_method', 'is_received')
#     search_fields = ('maHoaDon', 'user__username', 'email')
#     ordering = ('-created_at',)
#     inlines = [DetailInline, OrderEventInline]
#     readonly_fields = ('created_at', 'updated_at')
#     fieldsets = (
#         ('Order Information', {
#             'fields': ('user', 'tongTien', 'email', 'diaChi', 'status', 'is_received', 'payment_method')
#         }),
#         ('Additional Information', {
#             'classes': ('collapse',),
#             'fields': ('created_at', 'updated_at', 'loi', 'steps')
#         }),
#     )
@admin.register(HoaDon)
class HoaDonAdmin(admin.ModelAdmin):
    list_display = ('maHoaDon', 'user', 'tongTien', 'email', 'created_at', 'status', 'payment_method', 'is_received')
    list_filter = ('status', 'payment_method', 'is_received')
    search_fields = ('maHoaDon', 'user__username', 'email')
    ordering = ('-created_at',)
    inlines = [DetailInline, OrderEventInline]
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Thông tin đơn hàng', {
            'fields': ('user', 'tongTien', 'email', 'diaChi', 'status', 'is_received', 'payment_method')
        }),
        ('Thông tin bổ sung', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'loi')
        }),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Cập nhật tổng tiền đơn hàng
        total_amount = sum(
            detail.quantity * detail.product.productsize_set.get(size=detail.size).price
            for detail in form.instance.details.all()
        )
        form.instance.tongTien = total_amount
        form.instance.save()


# Feedback Admin
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('mess_id', 'user', 'email', 'phone_number', 'time')
    search_fields = ('user__username', 'email', 'message')
    ordering = ('-time',)

# Review Admin
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'rate', 'created_at', 'content')
    list_filter = ('rate', 'created_at')
    search_fields = ('user__username', 'product__title', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'created_at', 'updated_at')
    search_fields = ('title',)
    list_filter = ('type',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ShopInfo)
class ShopInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'open_time', 'close_time', 'is_open_weekend', 'ship_available')
    search_fields = ('name', 'address', 'phone_number')
    readonly_fields = ('created_at', "updated_at")

