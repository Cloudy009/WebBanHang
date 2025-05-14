import base64
from datetime import datetime, timedelta
from io import BytesIO
import locale
from django.contrib.auth.models import User
from django.utils import timezone
from matplotlib import pyplot as plt
from home.models import Category, Detail, HoaDon, Like, Product, ProductImage, ProductSize
from django.db.models import Sum, Count, F
from accounts.models import CustomUser

def get_top_selling_products():
    DEFAULT_IMAGE = '/static/images/logoCard.png'

    # Query để lấy 10 sản phẩm bán chạy nhất và thêm hình ảnh đầu tiên của sản phẩm
    top_selling_products = (
        Detail.objects
        .values('product__pro_id', 'product__title')  # Lấy ID và tên sản phẩm
        .annotate(total_sold=Sum('quantity'))  # Tổng số lượng bán của từng sản phẩm
        .order_by('-total_sold')[:10]  # Sắp xếp giảm dần và lấy 10 sản phẩm đầu tiên
    )

    # Lấy hình ảnh đầu tiên của mỗi sản phẩm
    for product in top_selling_products:
        product_id = product['product__pro_id']

        # Lấy ảnh
        product_image = ProductImage.objects.filter(product_id=product_id).first()
        product['image_pro'] = product_image.image if product_image else DEFAULT_IMAGE

        # Lấy giá đầu tiên (nếu có ProductSize)
        first_price = (
            ProductSize.objects.filter(product_id=product_id)
            .order_by('price')
            .values_list('price', flat=True)
            .first()
        )
        product['price'] = first_price if first_price is not None else 0.0

    print(top_selling_products)
    return top_selling_products

def get_trending_products():
    DEFAULT_IMAGE = '/static/images/logoCard.png'

    # Lấy top 10 sản phẩm phổ biến
    top_products = (
        Detail.objects
        .values('product__pro_id', 'product__title')
        .annotate(
            count=Count('product__pro_id', distinct=True),
            customer_count=Count('hoaDon__user', distinct=True)
        )
        .order_by('-count')[:10]
    )

    # Gắn hình ảnh và giá đầu tiên cho mỗi sản phẩm
    for product in top_products:
        product_id = product['product__pro_id']

        # Lấy ảnh
        product_image = ProductImage.objects.filter(product_id=product_id).first()
        product['image_pro'] = product_image.image if product_image else DEFAULT_IMAGE

        # Lấy giá đầu tiên (nếu có ProductSize)
        first_price = (
            ProductSize.objects.filter(product_id=product_id)
            .order_by('price')
            .values_list('price', flat=True)
            .first()
        )
        product['price'] = first_price if first_price is not None else 0.0

    return top_products
# GỢI Ý CHO KHÁCH HÀNG ĐÃ LOGIN
def get_user_recommended_products(user):
    # Lấy các sản phẩm mà người dùng đã mua trong các hóa đơn, tính tổng số lượng mua mỗi sản phẩm
    purchased_products = (
        Detail.objects
        .filter(hoaDon__user=user)  # Lọc theo hóa đơn của người dùng
        .values('product__pro_id', 'product__title')  # Lấy thông tin sản phẩm
        .annotate(total_quantity=Sum('quantity'))  # Tính tổng số lượng đã mua của mỗi sản phẩm
        .order_by('-total_quantity')  # Sắp xếp theo tổng số lượng mua (sản phẩm bán chạy nhất lên đầu)
    )

    # Thêm hình ảnh đầu tiên của mỗi sản phẩm
    for product in purchased_products:
        product_image = ProductImage.objects.filter(product_id=product['product__pro_id']).first()
        product['image_pro'] = product_image.image if product_image else None

    # Lấy 10 sản phẩm bán chạy nhất
    top_10_products = purchased_products[:10]

    return top_10_products

def get_liked_products_recommendations(user):
    # Lấy các sản phẩm mà người dùng đã like
    liked_products = (
        Like.objects
        .filter(user=user)
        .values('product__pro_id', 'product__category__cate_id')  # Chỉ lấy ID sản phẩm và danh mục
    )

    recommended_products = []

    # Nếu người dùng đã like ít nhất 1 sản phẩm
    if liked_products:
        # Lấy danh sách các danh mục mà người dùng đã like
        liked_categories = set(prod['product__category__cate_id'] for prod in liked_products)
        # Lấy danh sách các sản phẩm mà người dùng đã like (để loại trừ)
        liked_product_ids = set(prod['product__pro_id'] for prod in liked_products)

        # Lấy các sản phẩm trong cùng danh mục, ngoại trừ sản phẩm đã like
        recommended_products_queryset = Product.objects.filter(category__cate_id__in=liked_categories).exclude(
            pro_id__in=liked_product_ids
        )

        # Chuẩn bị danh sách sản phẩm với hình ảnh
        recommended_products = []
        for product in recommended_products_queryset[:10]:  # Lấy tối đa 5 sản phẩm
            image = ProductImage.objects.filter(product=product).first()
            recommended_products.append({
                'id': product.pro_id,
                'title': product.title,
                'image': image.image if image else None,
                'category': product.category.name,
            })

    return recommended_products

## TÍNH DASHBOARD USER
def calculate_order_summary(user):
    # Lấy tất cả các hóa đơn của người dùng hiện tại
    hoa_don_list = HoaDon.objects.filter(user=user)
    
    # Tính tổng số hóa đơn
    total_invoices = hoa_don_list.count()

    # Tính tổng tiền đã chi cho các hóa đơn của user
    total_spent = hoa_don_list.aggregate(total=Sum('tongTien'))['total'] or 0

    # Tính tổng tiền đã giảm giá cho các hóa đơn của user
    total_discount = 0
    for hoa_don in hoa_don_list:
        voucher = hoa_don.voucher
        if voucher:  
            total_discount += int(voucher.discount_amount * 100)

    return {
        'total_invoices': total_invoices,
        'total_spent': total_spent,
        'total_discount': total_discount
    }

def get_category_products():
    """
    Hàm lấy danh mục và danh sách sản phẩm theo từng danh mục
    """
    categories = Category.objects.prefetch_related('product_set').all()
    DEFAULT_IMAGE = '/static/images/logoCard.png'

    category_products = {}
    for category in categories:
        # Lấy tối đa 5 sản phẩm mỗi danh mục
        products = category.product_set.all()[:5]
        products_with_images = []
        for product in products:
            image_obj = ProductImage.objects.filter(product=product).first()
            image_url = image_obj.image if image_obj else DEFAULT_IMAGE

            products_with_images.append({
                'id': product.pro_id,
                'title': product.title,
                'image': image_url,
                'price': 18.00,  # Thay bằng product.original_price nếu muốn
            })
        category_products[category.name] = products_with_images

    return category_products


def calculate_month_revenue():
    # Lấy ngày hôm nay (dạng date)
    today = timezone.now().date()

    # Lấy thời gian bắt đầu của tháng (ngày 1 của tháng hiện tại)
    start_of_month = today.replace(day=1)

    # Lấy thời gian kết thúc của tháng (ngày cuối cùng của tháng hiện tại)
    next_month = today.replace(day=28) + timezone.timedelta(days=4)  # Đảm bảo luôn có ngày 1 của tháng tiếp theo
    end_of_month = next_month.replace(day=1) - timezone.timedelta(days=1)

    # Lọc các hóa đơn được tạo trong tháng này
    hoa_dons_this_month = HoaDon.objects.filter(
        created_at__gte=start_of_month, 
        created_at__lte=end_of_month
    )

    # Tính tổng doanh thu trong tháng này
    total_revenue_month = hoa_dons_this_month.aggregate(total_revenue=Sum('tongTien'))['total_revenue'] or 0

    return total_revenue_month

def calculate_day_revenue():
    # Lấy ngày hôm nay (dạng date)
    today = datetime.today().date()

    # Lấy thời gian bắt đầu của ngày hôm nay (00:00:00)
    start_of_day = datetime.combine(today, datetime.min.time())

    # Lấy thời gian kết thúc của ngày hôm nay (23:59:59.999999)
    end_of_day = datetime.combine(today, datetime.max.time())

    # Lọc các hóa đơn được tạo trong ngày hôm nay
    hoa_dons_today = HoaDon.objects.filter(
        created_at__gte=start_of_day, 
        created_at__lt=end_of_day
    )

    # Tính tổng doanh thu trong ngày hôm nay
    total_revenue_today = hoa_dons_today.aggregate(total_revenue=Sum('tongTien'))['total_revenue'] or 0

    return total_revenue_today

def calculate_daily_products_sold():
    # Lấy thời gian hiện tại
    now = datetime.now()

    # Lấy ngày hôm nay bắt đầu từ 00:00:00
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Lọc chi tiết sản phẩm đã bán trong ngày hôm nay
    total_products_sold_today = Detail.objects.filter(
        hoaDon__created_at__gte=start_of_day
    ).aggregate(total_sold=Sum('quantity'))['total_sold'] or 0

    return total_products_sold_today

def calculate_monthly_products_sold():
     # Lấy thời gian hiện tại
    now = datetime.now()

    # Tính ngày đầu tháng và cuối tháng
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_of_month = (first_day_of_month.replace(month=now.month + 1 if now.month < 12 else 1, year=now.year + 1 if now.month == 12 else now.year) - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)

    # Lọc chi tiết sản phẩm đã bán trong tháng này
    total_products_sold = Detail.objects.filter(
        hoaDon__created_at__gte=first_day_of_month,
        hoaDon__created_at__lt=last_day_of_month
    ).aggregate(total_sold=Sum('quantity'))['total_sold'] or 0

    return total_products_sold

def count_registered_users_today():
    now = datetime.now()

    # Lấy thời gian bắt đầu của ngày hôm nay (00:00:00)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Lọc người dùng đăng ký trong ngày hôm nay
    total_users_today = CustomUser.objects.filter(date_joined__gte=start_of_day).count()

    return total_users_today

def calculate_users_registered_this_month():
    now = datetime.now()
    
    # Lấy ngày đầu tháng (ngày 1 của tháng hiện tại)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Lọc người dùng đăng ký từ ngày đầu tháng đến nay
    total_users_this_month = CustomUser.objects.filter(date_joined__gte=start_of_month).count()

    return total_users_this_month

import plotly.express as px
import pandas as pd
from django.db.models.functions import ExtractMonth

def get_monthly_revenue(year):
    # Lấy tất cả hóa đơn trong năm
    start_of_year = datetime(year, 1, 1)
    end_of_year = datetime(year, 12, 31, 23, 59, 59)
    
    # Lọc các hóa đơn trong năm
    invoices = HoaDon.objects.filter(created_at__gte=start_of_year, created_at__lte=end_of_year)

    # Khởi tạo mảng doanh thu theo từng tháng (mặc định là 0)
    revenue = [0] * 12

    # Duyệt qua từng hóa đơn và tính doanh thu cho từng tháng
    for invoice in invoices:
        # Lấy tháng của hóa đơn
        month = invoice.created_at.month
        
        # Thêm doanh thu vào tháng tương ứng
        revenue[month - 1] += invoice.tongTien  # tháng 1 -> index 0, tháng 2 -> index 1, ...

    return revenue



def get_revenue_chart(year):
     # Giả sử đây là doanh thu hàng tháng (đơn vị: VND)
    revenue = get_monthly_revenue(year)  # Hàm này lấy doanh thu từ cơ sở dữ liệu
    months = [f'{i+1}' for i in range(12)]  # Các tháng trong năm

    # Tạo biểu đồ cột với Plotly
    fig = go.Figure()

    # Thêm cột biểu diễn doanh thu
    fig.add_trace(go.Bar(
        x=months,
        y=revenue,
        name='Doanh thu',
        marker=dict(
            color='rgb(0, 123, 255)',  # Màu sắc của cột (có thể thay đổi)
            line=dict(color='rgb(0, 70, 140)', width=2),  # Màu viền cột
            opacity=0.7  # Độ trong suốt của cột
        ),
        hovertemplate='%{y} VND<extra></extra>',  # Hiển thị thông tin khi hover
    ))

    # Tùy chỉnh layout (thiết lập tiêu đề, nhãn, và bố cục)
    fig.update_layout(
        title=f'Doanh thu theo tháng trong năm {year}',
        xaxis_title='Tháng',
        yaxis_title='Doanh thu (VND)',
        template='plotly_dark',  # Mẫu nền tối
        plot_bgcolor='rgb(28, 28, 28)',  # Màu nền của biểu đồ
        paper_bgcolor='rgb(28, 28, 28)',  # Màu nền của trang
        font=dict(color='white'),  # Màu chữ
        showlegend=False,
        height=300,
        xaxis=dict(
            tickangle=0  # Đảm bảo các nhãn tháng không bị xoay
        )
    )

    # Trả về biểu đồ dưới dạng HTML
    graph_html = fig.to_html(full_html=False)
    return graph_html

import plotly.graph_objects as go

def get_revenue_line_chart(year):
    revenue = get_monthly_revenue(year)

    # Doanh thu mục tiêu giả sử là 500,000 VND mỗi tháng
    target_revenue = [500000] * 12  # Mục tiêu doanh thu cố định

    # Các tháng trong năm
    months = [f'Tháng {i+1}' for i in range(12)]

    # Tạo biểu đồ đường với Plotly
    fig = go.Figure()

    # Thêm đường doanh thu thực tế
    fig.add_trace(go.Scatter(
        x=months,
        y=revenue,
        mode='lines+markers',
        name='Doanh thu thực tế',
        line=dict(color='blue'),
        marker=dict(size=6),
        text=[f'{r} VND' for r in revenue],  # Hiển thị doanh thu khi hover
        hoverinfo='text'
    ))

    # Thêm đường mục tiêu doanh thu
    fig.add_trace(go.Scatter(
        x=months,
        y=target_revenue,
        mode='lines',
        name='Mục tiêu doanh thu',
        line=dict(color='red', dash='dash'),  # Đường mục tiêu là đường chấm
    ))

    # Thiết lập tiêu đề và nhãn
    fig.update_layout(
        title=f'Doanh thu theo tháng trong năm {year}',
        xaxis_title='Tháng',
        yaxis_title='Doanh thu (VND)',
        template='plotly_dark'
    )

    # Trả về biểu đồ dưới dạng HTML
    graph_html = fig.to_html(full_html=False)

    return graph_html