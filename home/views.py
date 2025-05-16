from decimal import Decimal
import json
from arrow import now
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import requests
# from sqlalchemy import Transaction
from home.models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.contrib import messages
from .calculations import *

from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from django.contrib.auth import update_session_auth_hash, logout
from home.forms import *
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.db import transaction 
from django.conf import settings
from home.vnpay import vnpay
from chatApp.models import Room
import hashlib
import hmac
import json
import random

time = timezone.now()


@login_required
def inforCustomer(request):
    user = request.user

    # Lấy các HoaDon của người dùng
    hoa_dons = HoaDon.objects.filter(user=user)

    # Lấy các Detail liên quan đến các HoaDon của người dùng mà không có Review
    details_without_reviews = Detail.objects.filter(
        hoaDon__in=hoa_dons
    ).exclude(
        review__isnull=False
    )

    messages.success(request, "This is your admin page!")

    context = {
        'details': details_without_reviews,
        'messages': messages.get_messages(request),
    }

    return render(request, 'shop/inforCustomer.html', context)

@login_required
def dashboard(request):
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Fetch orders with total quantity for each order
    hoaDons = HoaDon.objects.filter(user=request.user).prefetch_related('events').annotate(total_products=Sum('detail__quantity'))
    
    # Lấy các Detail không có review
    details_without_reviews = Detail.objects.filter(
        hoaDon__in=hoaDons
    ).exclude(
        review__isnull=False
    )

    # Prepare order data with events for the template
    order_data = [
        {
            'id': order.maHoaDon,
            'arrival': order.created_at.strftime("%d/%m/%y"),
            'link': f"https://www.grasshoppers.lk/customers/action/track/{order.maHoaDon}",
            'steps': order.status,
            'events': [
                {
                    'time': event.time.strftime("%Y-%m-%d %I:%M:%S %p"),
                    'location': event.location,
                    'event': event.event
                }
                for event in order.events.all()
            ]
        }
        for order in hoaDons
    ]
    
    # Predefined countries list
    predefined_countries = ['USA', 'Canada', 'UK']
    is_custom_country = user_profile.country not in predefined_countries if user_profile.country else False
    
    # Password change form handling
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated.")
            logout(request)
            return redirect('formLogIn')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PasswordChangeForm(request.user)
    
    # Lấy các Thống kê của người dùng
    order_summary = calculate_order_summary(request.user)

    # Context for template rendering
    context = {
        'total_invoices': order_summary['total_invoices'],
        'total_spent': order_summary['total_spent'],
        'total_discount': order_summary['total_discount'],
        'user_profile': user_profile,
        'is_custom_country': is_custom_country,
        'form': form,
        'hoaDons': hoaDons,
        'orders': order_data,
        'details': details_without_reviews,  # Thêm vào context
        'messages': messages.get_messages(request),

    }

    return render(request, 'shop/dashboard.html', context)

@require_POST
@login_required
def confirm_receipt(request):
    order_id = request.POST.get('order_id')
    try:
        # Retrieve the order matching the provided ID and the logged-in user
        order = HoaDon.objects.get(maHoaDon=order_id, user=request.user)
        order.is_received = True  # Mark as received
        order.save()
        return JsonResponse({'status': 'success', 'message': 'Order receipt confirmed.'})
    except HoaDon.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found.'})

def home2(request):
    total_items = 0
    cart_items = []
    recommended_user_products = []
    liked_recommendations = []

    room_name = None

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
        total_items = cart_items.count()
        room = Room.objects.filter(users=request.user).first()
        room_name = room.name if room else None
        
        recommended_user_products = get_user_recommended_products(request.user)
        liked_recommendations = get_liked_products_recommendations(request.user)

    trending_products = get_trending_products()
    top_selling_products = get_top_selling_products()
    categories = Category.objects.all()
    category_products = get_category_products()

    DEFAULT_IMAGE = '/static/images/logoCard.png'

    new_products_raw = Product.objects.order_by('-created_at')[:10]
    new_products_with_images = []
    for product in new_products_raw:
        image = ProductImage.objects.filter(product=product).first()
        image_url = image.image if image else DEFAULT_IMAGE

        # Lấy giá nhỏ nhất trong các size (nếu có)
        prices = [ps.price for ps in product.productsize_set.all()]
        price = min(prices) if prices else (float(product.original_price) if product.original_price else 0.0)

        new_products_with_images.append({
            'id': product.pro_id,
            'title': product.title,
            'image': image_url,
            'price': price,
        })

    context = {
        'category_products': category_products,
        'categories': categories,
        'newProducts': new_products_with_images,
        'top_selling_products': top_selling_products,
        'trending_products': trending_products,
        'liked_recommendations': liked_recommendations,
        'recommended_user_products': recommended_user_products,
        'total_items': total_items,
        'cart_items': cart_items,
        'room_name': room_name
    }

    return render(request, 'shop/home.html', context)

def send_email(request):
    if not request.user.is_authenticated:
        messages.error(request, "Vui lòng đăng nhập để thực hiện chức năng này.")
        return redirect('homePage')  # hoặc redirect đến trang bạn muốn

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Lấy dữ liệu từ biểu mẫu
            name = form.cleaned_data['name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            user = request.user
            # Nội dung email
            email_content = f"Name: {name}\nPhone Number: {phone_number}\nEmail: {email}\nMessage: {message}"

            # Gửi email
            send_mail(
                'Contact Form Submission',
                email_content,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_TO_EMAIL],
                fail_silently=False,
            )

            message = Feedback.objects.create(
                user=user,
                email=email,
                phone_number=phone_number,
                message=message,
            )
            message.save()
            messages.success(request, f'Cảm ơn bạn {name} đã gửi email cho shop')

            # # Chuyển hướng hoặc hiển thị thông báo thành công
            return redirect('homePage')  # Thay 'success_page' bằng tên trang thành công của bạn

    else:
        messages.error(request, "Không tìm thấy Email hợp lệ")
        return redirect('homePage')


@login_required
def send_user_email(user_email, subject, message):
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        return True  # Gửi email thành công
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        try:
            product_id = request.POST.get("product_id")
            selected_size = request.POST.get("size", "S")  # Kích thước sản phẩm
            quantity = int(request.POST.get('quantity', 1))
            

            print(f"product_id: {product_id}, selected_size: {selected_size}, quantity: {quantity}")

            # Nhận các tùy chọn đường, trà, đá
            sugar = request.POST.get("sugar", "normal")
            tea = request.POST.get("tea", "normal")
            ice = request.POST.get("ice", "normal")

            product = get_object_or_404(Product, pro_id=product_id)
            size_option = ProductSize.objects.get(product=product, size=selected_size)

            user = request.user
            # Tìm kiếm xem có sản phẩm nào với kích thước và sản phẩm đã chọn
            cart_item = CartItem.objects.filter(
                user=user, 
                product=product,
                size=size_option.size,
                sugar=sugar, 
                tea=tea,
                ice=ice
            ).first()

            if cart_item:
                # Nếu đã tồn tại với cùng kích thước và tùy chọn, cộng dồn số lượng
                cart_item.quantity += quantity
                cart_item.save()
                messages.success(request, f'Đã cập nhật số lượng sản phẩm {cart_item.product.title} - {cart_item.size} trong giỏ hàng')
            else:
                # Nếu không tồn tại, tạo bản ghi mới
                new_cart_item = CartItem(
                    user=user,
                    product=product,
                    size=size_option.size,
                    quantity=quantity,
                    sugar=sugar,
                    tea=tea,
                    ice=ice
                )
                new_cart_item.save()
                messages.success(request, 'Đã thêm sản phẩm mới vào giỏ hàng')

            return redirect(product_detail, product_id)
        except ProductSize.DoesNotExist:
            messages.error(request, 'Kích thước không hợp lệ.')
            return redirect(product_detail, product_id)
    else:
        return redirect('homePage')
    
#CẬP NHẬT SỐ LƯỢNG PRODUCT TRONG ITEM
@login_required
def update_cart(request):
    try:
        if request.method== 'POST':
            user= request.user
            cart_items = CartItem.objects.filter(user= user)

            for cart_item in cart_items:
                selected_quantity = f'quantity_{cart_item.id}'
                newQuantity = int(request.POST.get(selected_quantity,1))
                cart_item.quantity = newQuantity
                cart_item.save()
        return redirect(checkOut)
    except Exception as e:
        print(str(e))

@login_required
@require_POST
def remove_item(request):
    try:
        data = json.loads(request.body)
        product_id = data.get("product_id")
        product = get_object_or_404(Product, pro_id=product_id)
        user = request.user

        # Tìm CartItem chứa Product cần xóa
        cart_item = CartItem.objects.filter(user=user, product=product).first()
        if cart_item:
            cart_item.delete()
            # Thêm thông báo đã xóa sản phẩm thành công vào messages
            success_message = "Xóa sản phẩm thành công"
            messages.success(request, success_message)
            return JsonResponse({"status": "success", "message": "Xóa sản phẩm thành công"})
        else:
            return JsonResponse({"status": "error", "message": "Sản phẩm không tồn tại trong giỏ hàng"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "error", "message": "Đã xảy ra lỗi khi xóa sản phẩm"})


@login_required
def view_cart(request):
    total_items = 0
    cart_items = []
    subtotal_amount = 0  # Tổng tiền trước giảm giá
    discount_amount = 0  # Số tiền giảm giá từ voucher
    total_amount = 0  # Tổng tiền sau giảm giá
    voucher_code = None  # Mã voucher

    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    total_items = cart_items.count()

    # Tính tổng tiền của giỏ hàng và tổng từng sản phẩm
    for item in cart_items:
        try:
            # Lấy giá của sản phẩm theo kích cỡ trong giỏ hàng
            product_size = ProductSize.objects.get(product=item.product, size=item.size)
            item.price = product_size.price  # Thêm giá của sản phẩm vào item
            item.total_price = product_size.price * item.quantity  # Tổng tiền cho từng item
            
            subtotal_amount += item.total_price  # Cộng tổng tiền trước giảm giá

        except ProductSize.DoesNotExist:
            # Nếu không tìm thấy giá cho sản phẩm theo kích cỡ, hiển thị lỗi
            messages.error(request, f"Không tìm thấy giá cho sản phẩm {item.product.title} với kích cỡ {item.size}")

    # Lấy thông tin voucher từ session (nếu có)
    if 'voucher_code' in request.session:
        voucher_code = request.session.get('voucher_code')
        discount_amount = float(request.session.get('voucher_discount', 0))

    # Tính tổng tiền sau khi áp dụng voucher
    total_amount = max(0, subtotal_amount - discount_amount)

    context = {
        'cart_items': cart_items,
        'subtotal_amount': subtotal_amount,  # Tổng tiền trước giảm giá
        'discount_amount': discount_amount,  # Số tiền giảm giá
        'total_amount': total_amount,  # Tổng tiền sau giảm giá
        'total_items': total_items,  # Tổng số sản phẩm trong giỏ hàng
        'voucher_code': voucher_code,  # Mã voucher từ session
    }

    return render(request, 'shop/cart_page.html', context)


@login_required
def checkOut(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    total_items = cart_items.count()

    # Nếu giỏ hàng trống, chuyển hướng về trang giỏ hàng
    if total_items == 0:
        messages.error(request, "Giỏ hàng của bạn đang trống.")
        return redirect('cart_Page')

    # Tính tổng tiền giỏ hàng dựa trên các sản phẩm
    total_amount = 0
    for item in cart_items:
        try:
            size_option = ProductSize.objects.get(product=item.product, size=item.size)
            item_price = size_option.price
            item.total_price = item_price * item.quantity
            item.save()
            total_amount += item.total_price
        except ProductSize.DoesNotExist:
            messages.error(request, 'Kích thước không hợp lệ cho một trong các sản phẩm trong giỏ hàng.')
            return redirect('cart_Page')

    # Xử lý voucher từ session
    voucher_code = request.session.get('voucher_code', None)
    voucher_discount = float(request.session.get('voucher_discount', 0))

    # Tính tổng tiền sau khi áp dụng voucher
    total_after_discount = max(0, total_amount - voucher_discount)

    # Lấy hoặc tạo thông tin UserProfile
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    # Truyền dữ liệu vào template
    context = {
        'cart_items': cart_items,
        'total_items': total_items,
        'total_amount': total_amount,
        'voucher_code': voucher_code,
        'voucher_discount': voucher_discount,
        'total_after_discount': total_after_discount,
        'user_profile': user_profile,
    }
    return render(request, 'shop/thanhToan_Page.html', context)


@login_required
@transaction.atomic  # Ensures all database actions are rolled back if an error occurs
def thanhToan(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    total_items = cart_items.count()

    # Redirect if the cart is empty
    if total_items == 0:
        messages.error(request, "Giỏ hàng của bạn đang trống.")
        return redirect('cart_Page')

    # Calculate total amount based on cart items
    total_amount = 0
    for item in cart_items:
        try:
            # Get the product size price for each cart item
            product_size = ProductSize.objects.get(product=item.product, size=item.size)
            item_price = product_size.price * item.quantity
            total_amount += item_price
        except ProductSize.DoesNotExist:
            messages.error(request, 'Kích thước không hợp lệ cho một trong các sản phẩm.')
            return redirect('cart_Page')

    # Get or create UserProfile for address details
    user_profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # Retrieve form data
        payment_method = request.POST.get('payment_method', 'credit')  # Default to 'credit' if not set
        selected_address = request.POST.get('address')
        # Check if user selected a saved address or a new one
        if selected_address == 'new':
            # Update UserProfile with new address information from form data
            user_profile.first_name = request.POST.get('first_name', user_profile.first_name)
            user_profile.last_name = request.POST.get('last_name', user_profile.last_name)
            user_profile.phone_number = request.POST.get('phone_number', user_profile.phone_number)
            user_profile.address = request.POST.get('address', user_profile.address)
            user_profile.city = request.POST.get('city', user_profile.city)
            user_profile.zip = request.POST.get('postal_code', user_profile.zip)
            user_profile.country = request.POST.get('country', user_profile.country)
            user_profile.save()

        # Create a new order (HoaDon)
        hoadon = HoaDon.objects.create(
            user=user,
            tongTien=total_amount,
            diaChi=user_profile.address,
            email=user_profile.email,
            status=False,  # Assuming 'False' means pending payment
            payment_method=payment_method  # Store selected payment method

        )

        # Add each cart item to the order's detail
        for item in cart_items:
            Detail.objects.create(
                hoaDon=hoadon,
                product=item.product,
                size=item.size,
                quantity=item.quantity
            )

        # Clear the cart after successful order creation
        cart_items.delete()

        # Display success message and redirect to a confirmation page or payment gateway
        messages.success(request, "Đặt hàng thành công. Đơn hàng của bạn đã được tạo.")
        return redirect('order_confirmation', hoadon_id=hoadon.maHoaDon)

    # If not a POST request, redirect back to checkout
    messages.error(request, "Lỗi khi thực hiện thanh toán.")
    return redirect('checkOut')

@login_required
def order_confirmation(request, hoadon_id):
    hoadon = get_object_or_404(HoaDon, maHoaDon=hoadon_id, user=request.user)
    return render(request, 'shop/order_confirmation.html', {'hoadon': hoadon})
#XÓA GIỎ HÀNG CỦA USER KHI THANH TOÁN THÀNH CÔNG
@require_POST
def transaction(request):
    try:
        user = request.user
        cart_items = CartItem.objects.filter(user= user)
        cart_items.delete()
        
        return JsonResponse({"status": "success", "message": "Deleted Items of {user} successfully"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


categories = Category.objects.all()
allProduct = Product.objects.all()

def get_reviews(product, request):
    star_filter = request.GET.get('stars', '')  # Lọc theo số sao
    sort_order = request.GET.get('sort', 'created_at')  # Sắp xếp theo số sao hoặc ngày tạo
    page_number = request.GET.get('page', 1)

    # Bắt đầu với danh sách review của sản phẩm
    reviews = Review.objects.filter(product=product)

    # Lọc theo số sao nếu có yêu cầu
    if star_filter:
        reviews = reviews.filter(rate=star_filter)

    # Sắp xếp review theo yêu cầu
    if sort_order == 'stars_asc':
        reviews = reviews.order_by('rate')
    elif sort_order == 'stars_desc':
        reviews = reviews.order_by('-rate')
    else:
        reviews = reviews.order_by('-created_at')  # Mặc định sắp xếp theo ngày tạo (mới nhất)

    # Phân trang với mỗi trang chứa 5 review
    paginator = Paginator(reviews, 5)
    page_obj = paginator.get_page(page_number)

    return page_obj

def get_product_by_id_or_name(product_id=None, product_name=None):
    """
    Get a product by its ID or name.
    :param product_id: The ID of the product (optional)
    :param product_name: The name of the product (optional)
    :return: Product object
    """
    if product_id:
        # Find product by ID
        return get_object_or_404(Product, pro_id=product_id)
    elif product_name:
        # Find product by name
        return get_object_or_404(Product, title__iexact=product_name)
    else:
        # If both are None, raise an exception
        raise ValueError("Either product_id or product_name must be provided.")

from django.db.models import Avg

@login_required
def product_detail(request, identifier):
    try:
        # Nếu identifier là số, tìm theo product_id
        product = get_product_by_id_or_name(product_id=int(identifier))
    except ValueError:
        # Nếu không phải số, tìm theo tên sản phẩm
        product = get_product_by_id_or_name(product_name=identifier)

    page_obj = get_reviews(product, request)

    # Lấy danh sách ảnh của sản phẩm từ ProductImage
    product_images = ProductImage.objects.filter(product=product)

    # Kiểm tra xem đây có phải là yêu cầu AJAX không
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Chuẩn bị phản hồi JSON cho yêu cầu AJAX
        review_data = [
            {
                'user': review.user.username,
                'rate': review.rate,
                'content': review.content,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for review in page_obj.object_list
        ]
        return JsonResponse({
            'reviews': review_data,
            'has_next': page_obj.has_next(),
            'page_number': page_obj.number,
            'total_pages': page_obj.paginator.num_pages,
            
        })
    
     # Tính trung bình sao từ reviews
    average_rating = Review.objects.filter(product=product).aggregate(average=Avg('rate'))['average']
    average_rating = round(average_rating, 1) if average_rating else 0  # Làm tròn 1 chữ số thập phân hoặc mặc định 0

    reviews = Review.objects.filter(product=product).order_by('-created_at')


    user_has_liked = Like.objects.filter(user=request.user, product=product).exists()

    context = {
        'product': product,
        'reviews': reviews,
        'average_rating': average_rating,  # Thêm trung bình sao vào context

        'user_has_liked': user_has_liked,  # Thêm thông tin về trạng thái like
        'page_obj': page_obj,
        'product_images': product_images,  # Thêm danh sách ảnh vào context

        'messages': messages.get_messages(request)
    }

    return render(request, 'shop/productDetail.html', context)


from django.core.paginator import Paginator
from django.shortcuts import render

from django.db.models import Q

def search_products(request):
    query = request.GET.get('q', '')
    if query:
        # Lọc sản phẩm dựa trên từ khóa tìm kiếm, lấy tối đa 10 sản phẩm
        products = Product.objects.filter(Q(title__icontains=query))[:10]
        results = [{'title': product.title} for product in products]  # Tạo danh sách kết quả
        return JsonResponse(results, safe=False)  # Trả về dưới dạng JSON
    return JsonResponse([], safe=False)  # Trả về mảng rỗng nếu không có kết quả


def product_list(request, category_id=None):
    DEFAULT_IMAGE = '/static/images/logoCard.png'

    category_id = category_id or request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_order = request.GET.get('sort', '')

    product_list = Product.objects.all()

    # Lọc theo danh mục
    if category_id:
        product_list = product_list.filter(category_id=category_id)

    # Lọc theo khoảng giá
    if min_price and max_price:
        try:
            min_price_val = float(min_price)
            max_price_val = float(max_price)
            product_list = product_list.filter(
                productsize__price__gte=min_price_val,
                productsize__price__lte=max_price_val
            ).distinct()
        except ValueError:
            pass

    # Sắp xếp theo giá
    if sort_order == 'price_asc':
        product_list = product_list.order_by('productsize__price')
    elif sort_order == 'price_desc':
        product_list = product_list.order_by('-productsize__price')

    # Phân trang
    paginator = Paginator(product_list, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    product_count = paginator.count

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        products = []
        for product in page_obj.object_list:
            product_image = ProductImage.objects.filter(product=product).first()
            image_url = product_image.image if product_image else DEFAULT_IMAGE

            # Tìm giá nhỏ nhất trong khoảng min-max (nếu có)
            price = None
            if min_price and max_price:
                try:
                    min_p = Decimal(min_price)
                    max_p = Decimal(max_price)
                    valid_prices = [
                        ps.price for ps in product.productsize_set.all()
                        if min_p <= ps.price <= max_p
                    ]
                    price = min(valid_prices) if valid_prices else None
                except:
                    pass
            else:
                prices = [ps.price for ps in product.productsize_set.all()]
                price = min(prices) if prices else None

            products.append({
                'id': product.pro_id,
                'title': product.title,
                'price': price,
                'category': product.category.name,
                'image': image_url,
                'detail_url': reverse('product-detail', kwargs={'identifier': product.pro_id}),
            })

        return JsonResponse({
            'products': products,
            'product_count': product_count,
            'has_next': page_obj.has_next(),
            'page_number': page_obj.number,
            'total_pages': paginator.num_pages
        })

    categories = Category.objects.all()
    return render(request, 'shop/food.html', {'page_obj': page_obj, 'categories': categories})

def category_list(request):
    categories = Category.objects.all().values('cate_id', 'name')
    return JsonResponse({'categories': list(categories)})

def testFiller(request):
    categories = Category.objects.all()
    allProduct = Product.objects.all()
    return render(request, 'shop/testFiller.html', {'categories': categories, 'allProduct': allProduct})


def get_admin():
    admin = User.objects.filter(is_superuser=True).first()
    if admin:
        return{
             'username': admin.username,
             'email': admin.email,
        }
    else:
         return None

def infor_profile(request):
    admin = get_admin()
    get_messages = Feedback.objects.all().order_by('-time')
    context = {
        'admin'        : admin,
        'messages'     : get_messages,
         }
    return render(request, 'pages/profile.html', context)

@login_required
def update_contact_info(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')  # Lấy email riêng từ form
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip')
        date_of_birth = request.POST.get('date_of_birth')
        country = request.POST.get('country_input') if request.POST.get('country_input') else request.POST.get('country_select')

        # Cập nhật các giá trị vào model UserProfile
        user_profile.first_name = first_name if first_name else user_profile.first_name
        user_profile.last_name = last_name if last_name else user_profile.last_name
        user_profile.email = email if email else user_profile.email  # Lưu email riêng
        user_profile.phone_number = phone_number if phone_number else user_profile.phone_number
        user_profile.address = address if address else user_profile.address
        user_profile.city = city if city else user_profile.city
        user_profile.zip = zip_code if zip_code else user_profile.zip
        user_profile.country = country if country else user_profile.country
        user_profile.date_of_birth = date_of_birth if date_of_birth else user_profile.date_of_birth

        is_primary = request.POST.get('check_primary_address')
        user_profile.is_primary = True if is_primary else False

        # Lưu thay đổi
        user_profile.save()

        return redirect(dashboard)

    return render(request, 'shop/dashboard.html', {'user_profile': user_profile})

@login_required
def add_review(request, product_id, hoadon_id, detail_id):
    product = get_object_or_404(Product, pro_id=product_id)
    hoaDon = get_object_or_404(HoaDon, maHoaDon = hoadon_id)
    detail = get_object_or_404(Detail, id = detail_id)
    user = request.user

    #  # Lấy thông tin size từ Detail
    # size = detail.size if hasattr(detail, 'size') else None

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        rate = int(request.POST.get('rating', 0))
        content = request.POST.get('opinion', '')

        # Kiểm tra xem người dùng đã đánh giá sản phẩm trước đó chưa
        existing_review = Review.objects.filter (
            user=user, 
            product=product, 
            hoadon = hoaDon, 
            detail = detail,
            # size=size 
        ).exists()

        if existing_review:
            messages.error(request, "You have already reviewed this product.")
        else:
            # Tạo đánh giá mới và lưu vào database
            review = Review.objects.create (
                user=user, 
                hoadon= hoaDon, 
                product=product, 
                rate=rate, 
                content=content, 
                detail = detail,
                # size=size  # Lưu thông tin size
            )

            review.save()

            messages.success(request, "Thank you for your review!")

        return redirect('dashboard')
    else:
        return redirect('dashboard')
    
# LẤY REVIEW KHÁCH HÀNG
@login_required
def product_review(request, product_id, hoadon_id):
    user = request.user
    product = get_object_or_404(Product, pro_id=product_id)
    hoadon = get_object_or_404(HoaDon, maHoaDon=hoadon_id, user=user)  # Lọc thêm `user` tại đây
    detail = Detail.objects.filter(hoaDon=hoadon, product=product).first()
    
    print(detail)
    
    return render(request, 'shop/review_Page.html', {'detail': detail})

def index(request):

    doanhThuNgay = calculate_day_revenue()
  
    context = {
        'doanhThuNgay'    : doanhThuNgay,
        }
    print('doanhThuNgay', doanhThuNgay),
    return render(request, 'pages/index.html', context)


def hmacsha512(key, data):
    byteKey = key.encode('utf-8')
    byteData = data.encode('utf-8')
    return hmac.new(byteKey, byteData, hashlib.sha512).hexdigest()


@csrf_exempt
def apply_voucher(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        voucher_code = data.get('voucher_code', '').strip()

        # Kiểm tra nếu mã voucher đã tồn tại trong session và trùng với mã nhập vào
        if 'voucher_code' in request.session and request.session['voucher_code'] == voucher_code:
            return JsonResponse({'status': 'error', 'message': 'Voucher đang được sử dụng.'})

        try:
            # Lấy voucher từ cơ sở dữ liệu
            voucher = Voucher.objects.get(code=voucher_code, is_active=True)

            # Kiểm tra điều kiện hợp lệ
            if not voucher.is_valid():
                return JsonResponse({'status': 'error', 'message': 'Voucher đã hết hạn hoặc không hoạt động.'})

            # Lưu voucher mới vào session
            request.session['voucher_code'] = voucher.code
            request.session['voucher_discount'] = float(voucher.discount_amount)

            # Phản hồi thành công
            return JsonResponse({
                'status': 'success',
                'discount': float(voucher.discount_amount),
                'voucher_code': voucher.code
            })

        except Voucher.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Voucher không tồn tại.'})

    return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ.'})



from geopy.distance import geodesic
from opencage.geocoder import OpenCageGeocode
API_KEY = "bfe7215d6c5342859e93b45320c10639"
geocoder = OpenCageGeocode(API_KEY)

#LẤY ĐỊA CHỈ
def get_address_from_coordinates(request):
    if request.method == 'POST':
        # Lấy dữ liệu từ request
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude and longitude:
            # Khởi tạo geocoder với OpenCage API
            geocoder = OpenCageGeocode(API_KEY)
            result = geocoder.reverse_geocode(latitude, longitude)

            if result:
                # Lấy địa chỉ từ kết quả trả về
                address = result[0]['formatted']
                return JsonResponse({'address': address})
            else:
                return JsonResponse({'error': 'Không thể tìm thấy địa chỉ từ tọa độ.'}, status=400)
        else:
            return JsonResponse({'error': 'Thiếu tọa độ.'}, status=400)
    return JsonResponse({'error': 'Yêu cầu không hợp lệ.'}, status=400)

#LẤY TẠO ĐỘ
def get_coordinates_from_address(address):
    """
    Lấy tọa độ (latitude, longitude) từ địa chỉ sử dụng OpenCage Geocoder API.
    """
    try:
        results = geocoder.geocode(address, language="vi", countrycode="VN")
        if results:
            latitude = results[0]['geometry']['lat']
            longitude = results[0]['geometry']['lng']
            return latitude, longitude
        else:
            print(f"Không tìm thấy địa chỉ: {address}")
            return None, None
    except Exception as e:
        print(f"Lỗi khi lấy tọa độ: {e}")
        return None, None

#Tính khoảng cách
def calculate_distance(coord1, coord2):
    """
    Tính khoảng cách giữa hai tọa độ (latitude, longitude) bằng km.
    """
    return geodesic(coord1, coord2).km

DEFAULT_CENTRAL_ADDRESS = "187 Tô Ngọc Vân, Linh Đông, Thủ Đức, Hồ Chí Minh, Việt Nam"
DEFAULT_CENTRAL_COORDINATES = get_coordinates_from_address(DEFAULT_CENTRAL_ADDRESS)

def check_user_distance(request):
    """
    View để kiểm tra khoảng cách từ người dùng đến địa chỉ trung tâm mặc định.
    """
    if request.method == "POST":
        try:
            # Đọc dữ liệu JSON từ request.body
            data = json.loads(request.body.decode('utf-8'))
            user_address = data.get('user_address', '')  # Địa chỉ người dùng

            if not user_address:
                return JsonResponse({"error": "Vui lòng nhập địa chỉ của bạn."}, status=400)

            # Chuyển địa chỉ người dùng thành tọa độ
            user_coordinates = get_coordinates_from_address(user_address)
            if user_coordinates == (None, None):
                return JsonResponse({"error": "Không thể xác định tọa độ từ địa chỉ người dùng."}, status=400)

            # Tính khoảng cách giữa tọa độ người dùng và tọa độ trung tâm
            distance = calculate_distance(DEFAULT_CENTRAL_COORDINATES, user_coordinates)
            print(distance)

            return JsonResponse({
                "distance": distance,
                "message": f"Khoảng cách giao hàng cách {distance:.2f} km."
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Dữ liệu gửi không hợp lệ."}, status=400)

    return JsonResponse({"error": "Phương thức không hợp lệ."}, status=405)

from django.db import transaction
@login_required
@transaction.atomic
def payment(request):
    if request.method == 'POST':
        print(request.POST)

    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    total_items = cart_items.count()

    # Redirect if the cart is empty
    if total_items == 0:
        messages.error(request, "Giỏ hàng của bạn đang trống.")
        return redirect('cart_Page')

    # Calculate total amount based on cart items
    total_amount = 0
    for item in cart_items:
        try:
            product_size = ProductSize.objects.get(product=item.product, size=item.size)
            item_price = product_size.price * item.quantity
            total_amount += item_price
        except ProductSize.DoesNotExist:
            messages.error(request, 'Kích thước không hợp lệ cho một trong các sản phẩm.')
            return redirect('cart_Page')

    # Get or create UserProfile for address details
    user_profile, _ = UserProfile.objects.get_or_create(user=user)

    # Tọa độ kho hàng (địa chỉ trung tâm)
    warehouse_coordinates = (10.855202098548403, 106.75056820137489)  # Ví dụ: tọa độ TP.HCM


    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'credit')
        selected_address = request.POST.get('address')

        if selected_address == 'new':
            # Check for missing address fields
            address = request.POST.get('address')
            if not address or address == 'new':
                messages.error(request, "Vui lòng nhập địa chỉ mới.")
                return redirect('checkOut')

            # Update user profile with new address
            user_profile.first_name = request.POST.get('first_name', user_profile.first_name)
            user_profile.last_name = request.POST.get('last_name', user_profile.last_name)
            user_profile.phone_number = request.POST.get('phone_number', user_profile.phone_number)
            user_profile.address = address
            user_profile.city = request.POST.get('city', user_profile.city)
            user_profile.zip = request.POST.get('postal_code', user_profile.zip)
            user_profile.country = request.POST.get('country', user_profile.country)
            user_profile.save()

            delivery_coordinates = get_coordinates_from_address(address)
            if delivery_coordinates == (None, None):
                messages.error(request, "Không thể xác định tọa độ từ địa chỉ mới. Vui lòng kiểm tra lại.")
                return redirect('checkOut')

        else:
            # Sử dụng địa chỉ đã lưu trong UserProfile
            if not user_profile.address or not user_profile.city or not user_profile.country:
                messages.error(request, "Không có địa chỉ nào được lưu.")
                return redirect('checkOut')

            # Lấy tọa độ từ địa chỉ đã lưu
            delivery_coordinates = get_coordinates_from_address(user_profile.address)

            if delivery_coordinates == (None, None):
                messages.error(request, "Không thể xác định tọa độ từ địa chỉ đã lưu. Vui lòng kiểm tra lại.")
                return redirect('checkOut')

        # Tính khoảng cách
        distance = calculate_distance(warehouse_coordinates, delivery_coordinates)
        if distance > 5:
            messages.error(request, "Địa chỉ giao hàng nằm ngoài bán kính 5km.")
            return redirect('checkOut')

        # Voucher handling
        # Handle voucher from session
        discount_amount = 0
        used_voucher = None
        if 'voucher_code' in request.session:
            voucher_code = request.session['voucher_code']
            try:
                voucher = Voucher.objects.get(code=voucher_code, is_active=True)

                # Check if voucher is still valid
                if voucher.expiration_date and voucher.expiration_date < now():
                    messages.error(request, "Mã voucher đã hết hạn.")
                    del request.session['voucher_code']  # Xóa voucher khỏi session
                    del request.session['voucher_discount']
                    return redirect('checkOut')

                if total_amount < voucher.min_spend:
                    messages.error(request, f"Bạn cần chi tiêu tối thiểu {voucher.min_spend} VND để sử dụng mã voucher này.")
                    del request.session['voucher_code']  # Xóa voucher khỏi session
                    del request.session['voucher_discount']
                    return redirect('checkOut')

                # Apply discount
                discount_amount = min(voucher.discount_amount, total_amount)
                total_amount -= discount_amount
                used_voucher = voucher
            except Voucher.DoesNotExist:
                messages.error(request, "Mã voucher không hợp lệ hoặc không tồn tại.")
                del request.session['voucher_code']  # Xóa voucher khỏi session nếu không hợp lệ
                del request.session['voucher_discount']
                return redirect('checkOut')

        # Create a new order (HoaDon)
        hoadon = HoaDon.objects.create(
            user=user,
            tongTien=total_amount,
            diaChi=user_profile.address,
            email=user_profile.email,
            status=False,
            payment_method=payment_method
        )

        # Associate the voucher with the order (if applicable)
        if used_voucher:
            hoadon.voucher = used_voucher
            hoadon.save()
            used_voucher.is_active = False
            used_voucher.save()

        # Add cart items to order details
        for item in cart_items:
            Detail.objects.create(
                hoaDon=hoadon,
                product=item.product,
                size=item.size,
                quantity=item.quantity,
                tea=item.tea,
                sugar=item.sugar,
                ice=item.ice,
            )
        if payment_method == 'credit':

            # Build VNPAY payment URL
            ipaddr = get_client_ip(request)
            vnp = vnpay()
            vnp.requestData['vnp_Version'] = '2.1.0'
            vnp.requestData['vnp_Command'] = 'pay'
            vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
            vnp.requestData['vnp_Amount'] = int(total_amount * 100)  # Multiply by 100 as required by VNPAY
            vnp.requestData['vnp_CurrCode'] = 'VND'
            vnp.requestData['vnp_TxnRef'] = hoadon.maHoaDon  # Use order ID as transaction reference
            vnp.requestData['vnp_OrderInfo'] = "Thanh toán hóa đơn #%s" % hoadon.maHoaDon
            vnp.requestData['vnp_OrderType'] = "topup"
            vnp.requestData['vnp_Locale'] = 'vn'
            vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
            vnp.requestData['vnp_IpAddr'] = ipaddr
            vnp.requestData['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL

            # Generate payment URL
            vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET_KEY)
            print("Redirecting to VNPAY:", vnpay_payment_url)

            # Clear the cart after order creation
            cart_items.delete()

            # Redirect to VNPAY payment gateway
            return redirect(vnpay_payment_url)
        
        else:
            cart_items.delete()
            # Handle non-credit payment methods
            messages.success(request, "Đặt hàng thành công. Đơn hàng của bạn đã được tạo.")
            return redirect('order_confirmation', hoadon_id=hoadon.maHoaDon)
        
    # If not POST, render the payment page
    return render(request, "vnpay/payment.html", {"title": "Thanh toán"})

def payment_ipn(request):
    inputData = request.GET
    if inputData:
        vnp = vnpay()
        vnp.responseData = inputData.dict()
        order_id = inputData['vnp_TxnRef']
        amount = inputData['vnp_Amount']
        order_desc = inputData['vnp_OrderInfo']
        vnp_TransactionNo = inputData['vnp_TransactionNo']
        vnp_ResponseCode = inputData['vnp_ResponseCode']
        vnp_TmnCode = inputData['vnp_TmnCode']
        vnp_PayDate = inputData['vnp_PayDate']
        vnp_BankCode = inputData['vnp_BankCode']
        vnp_CardType = inputData['vnp_CardType']
        if vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
            # Check & Update Order Status in your Database
            # Your code here
            firstTimeUpdate = True
            totalamount = True
            if totalamount:
                if firstTimeUpdate:
                    if vnp_ResponseCode == '00':
                        print('Payment Success. Your code implement here')
                    else:
                        print('Payment Error. Your code implement here')

                    # Return VNPAY: Merchant update success
                    result = JsonResponse({'RspCode': '00', 'Message': 'Confirm Success'})
                else:
                    # Already Update
                    result = JsonResponse({'RspCode': '02', 'Message': 'Order Already Update'})
            else:
                # invalid amount
                result = JsonResponse({'RspCode': '04', 'Message': 'invalid amount'})
        else:
            # Invalid Signature
            result = JsonResponse({'RspCode': '97', 'Message': 'Invalid Signature'})
    else:
        result = JsonResponse({'RspCode': '99', 'Message': 'Invalid request'})

    return result

def payment_return(request):
    inputData = request.GET

    # Log thông tin nhận được từ VNPAY
    print(f"Received VNPAY response: {inputData}")

    if inputData:
        vnp = vnpay()
        vnp.responseData = inputData.dict()

        # Lấy các tham số cần thiết
        order_id = inputData.get('vnp_TxnRef')
        amount = int(inputData.get('vnp_Amount', 0)) / 100
        order_desc = inputData.get('vnp_OrderInfo', 'Không có mô tả')
        vnp_TransactionNo = inputData.get('vnp_TransactionNo', 'N/A')
        vnp_ResponseCode = inputData.get('vnp_ResponseCode', None)
        vnp_TransactionStatus = inputData.get('vnp_TransactionStatus', 'N/A')
        vnp_PayDate = inputData.get('vnp_PayDate', 'N/A')
        vnp_BankCode = inputData.get('vnp_BankCode', 'N/A')
        vnp_CardType = inputData.get('vnp_CardType', 'N/A')

        # Kiểm tra nếu thiếu thông tin bắt buộc
        if not order_id or not vnp_ResponseCode:
            return render(request, "vnpay/payment_return.html", {
                "title": "Kết quả thanh toán",
                "result": "Lỗi",
                "msg": "Thiếu thông tin bắt buộc trong phản hồi",
                "order_id": order_id or "Không xác định",
                "amount": amount,
                "order_desc": order_desc,
                "vnp_TransactionNo": vnp_TransactionNo
            })

        # Kiểm tra checksum
        if vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
            if vnp_ResponseCode == "00" and vnp_TransactionStatus == "00":  # Giao dịch thành công
                return render(request, "vnpay/payment_return.html", {
                    "title": "Kết quả thanh toán",
                    "result": "Thành công",
                    "order_id": order_id,
                    "amount": amount,
                    "order_desc": order_desc,
                    "vnp_TransactionNo": vnp_TransactionNo,
                    "vnp_ResponseCode": vnp_ResponseCode
                })
            else:  # Giao dịch thất bại
                return render(request, "vnpay/payment_return.html", {
                    "title": "Kết quả thanh toán",
                    "result": "Lỗi",
                    "order_id": order_id,
                    "amount": amount,
                    "order_desc": order_desc,
                    "vnp_TransactionNo": vnp_TransactionNo,
                    "vnp_ResponseCode": vnp_ResponseCode,
                    "msg": f"Giao dịch không thành công. Trạng thái: {vnp_TransactionStatus}"
                })
        else:  # Sai checksum
            return render(request, "vnpay/payment_return.html", {
                "title": "Kết quả thanh toán",
                "result": "Lỗi",
                "order_id": order_id,
                "amount": amount,
                "order_desc": order_desc,
                "vnp_TransactionNo": vnp_TransactionNo,
                "msg": "Sai checksum. Dữ liệu có thể bị thay đổi."
            })
    else:
        return render(request, "vnpay/payment_return.html", {
            "title": "Kết quả thanh toán",
            "result": "Lỗi",
            "msg": "Không nhận được dữ liệu phản hồi từ VNPAY"
        })


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

n = random.randint(10**11, 10**12 - 1)
n_str = str(n)
while len(n_str) < 12:
    n_str = '0' + n_str


def query(request):
    if request.method == 'GET':
        return render(request, "query.html", {"title": "Kiểm tra kết quả giao dịch"})

    url = settings.VNPAY_API_URL
    secret_key = settings.VNPAY_HASH_SECRET_KEY
    vnp_TmnCode = settings.VNPAY_TMN_CODE
    vnp_Version = '2.1.0'

    vnp_RequestId = n_str
    vnp_Command = 'querydr'
    vnp_TxnRef = request.POST['order_id']
    vnp_OrderInfo = 'kiem tra gd'
    vnp_TransactionDate = request.POST['trans_date']
    vnp_CreateDate = datetime.now().strftime('%Y%m%d%H%M%S')
    vnp_IpAddr = get_client_ip(request)

    hash_data = "|".join([
        vnp_RequestId, vnp_Version, vnp_Command, vnp_TmnCode,
        vnp_TxnRef, vnp_TransactionDate, vnp_CreateDate,
        vnp_IpAddr, vnp_OrderInfo
    ])

    secure_hash = hmac.new(secret_key.encode(), hash_data.encode(), hashlib.sha512).hexdigest()

    data = {
        "vnp_RequestId": vnp_RequestId,
        "vnp_TmnCode": vnp_TmnCode,
        "vnp_Command": vnp_Command,
        "vnp_TxnRef": vnp_TxnRef,
        "vnp_OrderInfo": vnp_OrderInfo,
        "vnp_TransactionDate": vnp_TransactionDate,
        "vnp_CreateDate": vnp_CreateDate,
        "vnp_IpAddr": vnp_IpAddr,
        "vnp_Version": vnp_Version,
        "vnp_SecureHash": secure_hash
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = json.loads(response.text)
    else:
        response_json = {"error": f"Request failed with status code: {response.status_code}"}

    return render(request, "query.html", {"title": "Kiểm tra kết quả giao dịch", "response_json": response_json})

def refund(request):
    if request.method == 'GET':
        return render(request, "refund.html", {"title": "Hoàn tiền giao dịch"})

    url = settings.VNPAY_API_URL
    secret_key = settings.VNPAY_HASH_SECRET_KEY
    vnp_TmnCode = settings.VNPAY_TMN_CODE
    vnp_RequestId = n_str
    vnp_Version = '2.1.0'
    vnp_Command = 'refund'
    vnp_TransactionType = request.POST['TransactionType']
    vnp_TxnRef = request.POST['order_id']
    vnp_Amount = request.POST['amount']
    vnp_OrderInfo = request.POST['order_desc']
    vnp_TransactionNo = '0'
    vnp_TransactionDate = request.POST['trans_date']
    vnp_CreateDate = datetime.now().strftime('%Y%m%d%H%M%S')
    vnp_CreateBy = 'user01'
    vnp_IpAddr = get_client_ip(request)

    hash_data = "|".join([
        vnp_RequestId, vnp_Version, vnp_Command, vnp_TmnCode, vnp_TransactionType, vnp_TxnRef,
        vnp_Amount, vnp_TransactionNo, vnp_TransactionDate, vnp_CreateBy, vnp_CreateDate,
        vnp_IpAddr, vnp_OrderInfo
    ])

    secure_hash = hmac.new(secret_key.encode(), hash_data.encode(), hashlib.sha512).hexdigest()

    data = {
        "vnp_RequestId": vnp_RequestId,
        "vnp_TmnCode": vnp_TmnCode,
        "vnp_Command": vnp_Command,
        "vnp_TxnRef": vnp_TxnRef,
        "vnp_Amount": vnp_Amount,
        "vnp_OrderInfo": vnp_OrderInfo,
        "vnp_TransactionDate": vnp_TransactionDate,
        "vnp_CreateDate": vnp_CreateDate,
        "vnp_IpAddr": vnp_IpAddr,
        "vnp_TransactionType": vnp_TransactionType,
        "vnp_TransactionNo": vnp_TransactionNo,
        "vnp_CreateBy": vnp_CreateBy,
        "vnp_Version": vnp_Version,
        "vnp_SecureHash": secure_hash
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = json.loads(response.text)
    else:
        response_json = {"error": f"Request failed with status code: {response.status_code}"}

    return render(request, "refund.html", {"title": "Kết quả hoàn tiền giao dịch", "response_json": response_json})

# your_app/views.py

from rest_framework import viewsets
from API.serializers import ReviewSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

@login_required
@csrf_exempt
def like_product(request):
    try:
        data = json.loads(request.body)
        product_id = data.get("product_id")
        print(product_id)
        product = get_object_or_404(Product, pro_id=product_id)
        user = request.user

        # Kiểm tra xem sản phẩm đã được thích bởi người dùng chưa
        like, created = Like.objects.get_or_create(user=user, product=product)

        if created:
            # Thích sản phẩm thành công
            return JsonResponse({"liked": True})
        else:
            # Đã thích rồi, bỏ thích sản phẩm
            like.delete()
            return JsonResponse({"liked": False})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "error", "message": "Đã xảy ra lỗi khi xử lý yêu cầu"})

@login_required
def favorite_products(request):
    user = request.user
    liked_products = Like.objects.filter(user=user).select_related('product')
    products = [like.product for like in liked_products]

    # Phân trang
    paginator = Paginator(products, 12)  # 12 sản phẩm mỗi trang
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Nếu yêu cầu là AJAX, trả về JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_list = [
            {
                'id': product.pro_id,
                'title': product.title,
                'image': product.image_pro,
                'price': product.price if hasattr(product, 'price') else "Liên hệ",
                'detail_url': reverse('product-detail', kwargs={'identifier': product.pro_id}),  # Thêm URL chi tiết sản phẩm

            }
            for product in page_obj
        ]
        return JsonResponse({
            'products': product_list,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_number': page_obj.number,
            'total_pages': paginator.num_pages,
        })

    # Trả về trang HTML
    return render(request, 'shop/liked_Products_Page.html', {'favorite_products': page_obj})

@csrf_exempt
@login_required
def remove_favorite(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        product = get_object_or_404(Product, pro_id=product_id)
        user = request.user

        # Xóa yêu thích
        Like.objects.filter(user=user, product=product).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_cart_items(request):
    # Lấy tất cả các sản phẩm trong giỏ hàng của người dùng
    cart_items = CartItem.objects.filter(user=request.user)  # Giả sử người dùng đã đăng nhập

    # Tính toán tổng số lượng sản phẩm và tổng giá trị
    total_items = cart_items.count()
    total_amount = 0

    cart_items_data = []
    for item in cart_items:
        # Tìm ProductSize tương ứng với sản phẩm và kích cỡ
        product_size = ProductSize.objects.get(product=item.product, size=item.size)
        item_total_price = product_size.price * item.quantity
        total_amount += item_total_price

        cart_items_data.append({
            'id': item.product.pro_id,
            'title': item.product.title,
            'price': product_size.price,  # Giá sản phẩm theo kích cỡ
            'size': item.size,  # Kích cỡ
            'quantity': item.quantity,  # Số lượng
            'total_price': item_total_price  # Tổng giá cho từng sản phẩm
        })

    # Trả về dữ liệu giỏ hàng dưới dạng JSON
    return JsonResponse({
        'total_items': total_items,
        'cart_items': cart_items_data,
        'total_amount': total_amount,  # Tổng số tiền
    })




# Nếu giỏ hàng trống
def get_empty_cart_data(request):
    return JsonResponse({'cart_items': [], 'total_amount': 0})