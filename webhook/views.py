# webhook/views.py
import json
import re
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from home.models import CartItem, Category, Product, HoaDon, Detail, ProductSize, Policy, ShopInfo  # Import model từ app home
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
User = get_user_model()

def checkProduct(product_name):
    """Kiểm tra sự tồn tại của sản phẩm trong cơ sở dữ liệu"""
    return Product.objects.filter(title__icontains=product_name)

# THÔNG TIN SẢN PHẨM

def checkProduct_custom(product_name):
    product = Product.objects.filter(title__icontains=product_name).first()
    if not product:
        normalized_input = normalize_product_name(product_name)
        words = normalized_input.split()  # Tách từ theo khoảng trắng
        max_words = 6  # Tối đa 6 từ
        matched_products = None
        matched_products_2 = None

        # Kiểm tra lần lượt từ tổ hợp 3 từ, rồi thêm vào từ thứ 4, thứ 5, ... nếu không có kết quả
        for i in range(3, min(max_words + 1, len(words) + 1)):
            search_term = " ".join(words[:i])  # Tạo tổ hợp tìm kiếm
            matched_products = Product.objects.filter(title__icontains=search_term)

            if matched_products.exists():
                product = matched_products.first()
                break  # Nếu có kết quả, thoát khỏi vòng lặp

        # Nếu không tìm thấy, thử với matched_products_2 (sử dụng thay thế 'y' bằng 'i')
        if not matched_products or not matched_products.exists():
            normalized_input_2 = replace_y_with_i(normalized_input)
            words_2 = normalized_input_2.split()  # Tách từ của normalized_input_2
            for i in range(3, min(max_words + 1, len(words_2) + 1)):
                search_term_2 = " ".join(words_2[:i])  # Tạo tổ hợp tìm kiếm cho matched_products_2
                matched_products_2 = Product.objects.filter(title__icontains=search_term_2)
                if matched_products_2.exists():
                    product = matched_products_2.first()
                    break  # Nếu có kết quả, thoát khỏi vòng lặp
    return product



#LẤY TẤT CẢ THÔNG TIN
#Câu test: print(get_product_details("list"))
def get_product_details(product_name):
    response_text = ""
    if not product_name:
        response_text += "Bạn chưa cung cấp tên sản phẩm."
    else:
        for name in product_name:
            print("Tên sản phẩm:", name)
            if not product_name:
                response_text += "Bạn chưa cung cấp tên sản phẩm."

            product = checkProduct_custom(name)
            if not product:
                response_text += f"Sản phẩm {name} không tìm thấy."
            else:
                sizes = ProductSize.objects.filter(product=product)

                # Kiểm tra thông tin kích cỡ
                if not sizes.exists():
                    response_text +=  f"Thông tin sản phẩm: {product.title}. Hiện chưa có thông tin về kích cỡ và giá cả."

                # Thông tin kích cỡ và giá
                size_info = "\n".join([f"- Size {size.size}: {size.price} VNĐ" for size in sizes])

                # Bổ sung các thông tin khác từ model Product
                response_text += f"""
                🏷️ Thông tin sản phẩm: {product.title}:
                📝 - Mô tả: {product.description or 'Chưa có mô tả'}
                🧵 - Chất liệu: {product.material or 'Chưa có thông tin về chất liệu'}
                💲 - Chi tiết size - giá: {size_info}
                """
    return response_text


#LẤY GIÁ SẢN 

#Câu test: print(get_product_price("Bánh mỳ chã cá"))
def get_product_price(product_name):
    response_text = ""
    if not product_name:
        response_text += "Bạn chưa cung cấp tên sản phẩm."
    else:
        response_text +=  f" Mình gửi bạn giá các sản phẩm bên mình nha: \n"
        for name in product_name:
            if not product_name:
                response_text += "Bạn chưa cung cấp tên sản phẩm."

            product = checkProduct_custom(name)
            if not product:
                response_text += f"Sản phẩm {name} không tìm thấy."

            sizes = ProductSize.objects.filter(product=product)

            if not sizes.exists():
                return f"Thông tin sản phẩm: {product.title}. Hiện chưa có thông tin về kích cỡ và giá cả."

            size_info = "\n".join([f" \n Size {size.size} - {size.price}VNĐ " for size in sizes])
            response_text +=  f" 🔎 Thông tin giá của {product.title} : \n{size_info} "
    return response_text

#LẤY THÔNG TIN SẢN PHẨM
from unidecode import unidecode

def normalize_product_name(name: str) -> str:
    """Chuẩn hóa tên sản phẩm, loại bỏ dấu và chuyển thành chữ thường."""
    return unidecode(name.strip().lower())

def get_similar_products(keyword: str, limit: int = 10):
    return Product.objects.filter(title__icontains=keyword).order_by('title')[:limit]

def replace_y_with_i(name: str) -> str:
    """Thay thế tất cả các ký tự 'y' thành 'i' trong chuỗi."""
    name = unidecode(name.strip().lower())
    return name.replace('y', 'i').replace('Y', 'I')  # Thay thế cả chữ hoa và chữ thường

def get_product_info_response(parameters: dict, field: str) -> str:
    """
    Trả về thông tin của sản phẩm từ intent 'product.requestDescription' hoặc 'product.requestMaterial'.
    Nếu không tìm thấy, gợi ý 10 sản phẩm tương tự nhất.
    :param parameters: Các tham số từ người dùng (bao gồm tên sản phẩm).
    :param field: Tên trường cần lấy ('description' hoặc 'material').
    :return: Thông tin mô tả hoặc vật liệu của sản phẩm.
    """
    try:
        product_names = parameters.get("product-name", [])
        user_input = product_names[0].strip().lower() if product_names else ""

        if not user_input:
            return "🔎 Bạn vui lòng cung cấp tên sản phẩm để mình mô tả rõ hơn nhé!"

        # Chuẩn hóa tên người dùng nhập
        normalized_input = normalize_product_name(user_input)
        words = normalized_input.split()  # Tách từ theo khoảng trắng
        max_words = 6  # Tối đa 6 từ
        matched_products = None
        matched_products_2 = None

        # Kiểm tra lần lượt từ tổ hợp 3 từ, rồi thêm vào từ thứ 4, thứ 5, ... nếu không có kết quả
        for i in range(3, min(max_words + 1, len(words) + 1)):
            search_term = " ".join(words[:i])  # Tạo tổ hợp tìm kiếm
            matched_products = Product.objects.filter(title__icontains=search_term)

            if matched_products.exists():
                break  # Nếu có kết quả, thoát khỏi vòng lặp

        # Nếu không tìm thấy, thử với matched_products_2 (sử dụng thay thế 'y' bằng 'i')
        if not matched_products or not matched_products.exists():
            normalized_input_2 = replace_y_with_i(normalized_input)
            words_2 = normalized_input_2.split()  # Tách từ của normalized_input_2
            for i in range(3, min(max_words + 1, len(words_2) + 1)):
                search_term_2 = " ".join(words_2[:i])  # Tạo tổ hợp tìm kiếm cho matched_products_2
                matched_products_2 = Product.objects.filter(title__icontains=search_term_2)

                if matched_products_2.exists():
                    break  # Nếu có kết quả, thoát khỏi vòng lặp

        # Nếu không tìm thấy sản phẩm
        if not matched_products and not matched_products_2:
            similar_products = get_similar_products(normalized_input[:4])
            if not similar_products:
                return f"❌ Mình không tìm thấy sản phẩm nào gần giống với \"{user_input}\" cả 😥."

            suggestion_text = "\n• " + "\n• ".join([p.title for p in similar_products])
            return (
                f"🤔 Mình chưa tìm thấy sản phẩm \"{user_input}\".\n"
                f"🔍 Tuy nhiên, bạn có muốn xem các sản phẩm tương tự sau không:\n"
                f"{suggestion_text}\n\n"
                "👉 Hãy nói rõ tên sản phẩm bạn muốn tìm để mình mô tả chính xác hơn nhé!"
            )

        # Nếu tìm thấy chính xác 1 sản phẩm
        if matched_products and matched_products.count() == 1:
            product = matched_products.first()
            if not getattr(product, field):
                return f"ℹ️ Sản phẩm **{product.title}** hiện chưa có thông tin {field} chi tiết."
            return f"📄 Thông tin sản phẩm **{product.title}**:\n{getattr(product, field)}"

        # Nếu tìm thấy chính xác 1 sản phẩm từ matched_products_2
        if matched_products_2 and matched_products_2.count() == 1:
            product = matched_products_2.first()
            if not getattr(product, field):
                return f"ℹ️ Sản phẩm **{product.title}** hiện chưa có thông tin {field} chi tiết."
            return f"📄 Thông tin sản phẩm **{product.title}**:\n{getattr(product, field)}"

        # Nếu có nhiều sản phẩm khớp
        product_list = "\n• " + "\n• ".join([p.title for p in matched_products])
        return (
            f"🧐 Bạn đang tìm sản phẩm nào? Có nhiều sản phẩm liên quan đến \"{user_input}\":\n"
            f"{product_list}\n\n"
            "👉 Vui lòng cung cấp đầy đủ tên sản phẩm để mình mô tả chính xác hơn nhé!"
        )

    except Exception as e:
        print("LỖI MÔ TẢ SẢN PHẨM:", e)
        return "⚠️ Có lỗi xảy ra khi truy xuất thông tin sản phẩm. Bạn vui lòng thử lại sau nhé!"


#LẤY SẢN PHẨM MỚI NHẤT
def get_newest_products():
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Giả sử model Product có trường created_at
    newest_products = Product.objects.filter(created_at__gte=start_of_month).order_by('-created_at')

    if not newest_products.exists():
        return "Không có sản phẩm mới trong tháng này."

    response = "Dưới đây là các sản phẩm mới nhất trong tháng này:\n"
    for product in newest_products:
        response += f"- {product.name}\n"

    return response

def get_menu():
    products = Product.objects.all()
    if products.exists():
        response_text = "Danh sách tất cả sản phẩm:\n"
        for product in products:
            response_text += f"- {product.title}"
    else:
        response_text = "Không có sản phẩm nào."
    return response_text

def get_cate_menu(cate):
    #Kiểm tra xem cate có giá trị hay không vì cate là mảng nên
    if cate != None:
        for i in cate:
            cate_name = Category.objects.get(cate_id=i).name
            products = Product.objects.filter(category_id=i)
            if products.exists():
                response_text = f"Danh sách sản phẩm thuộc danh mục * {cate_name} *: \n"
                for product in products:
                    response_text += f" - {product.title} - "
            else:
                response_text = f"Không có sản phẩm nào thuộc danh mục {i}."
    else:
        products = Product.objects.all()
        if products.exists():
            response_text = "Danh sách tất cả sản phẩm:\n"
            for product in products:
                response_text += f" - {product.title} - "
        else:
            response_text = "Không có sản phẩm nào."
        
    return response_text

#Function About Cart
def get_view_cart(username):
    try:
        user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        return "Không tìm thấy người dùng."

    cart_items = CartItem.objects.filter(user=user)[:5]

    if cart_items:
        response_text = "🛒 Danh sách sản phẩm trong giỏ hàng:\n"
        total_quantity = 0
        total_price = 0

        for item in cart_items:
            product = item.product
            size_value = item.size  # ví dụ: 'M', 'L'

            # Tìm ProductSize tương ứng
            try:
                product_size = ProductSize.objects.get(product=product, size=size_value)
                price = product_size.price
            except ProductSize.DoesNotExist:
                price = 0  # hoặc xử lý lỗi khác nếu muốn

            quantity = item.quantity
            subtotal = price * quantity

            total_quantity += quantity
            total_price += subtotal

            response_text += (
                f"- {product.title} (Size: {size_value}), "
                f"Giá: {price:,} VNĐ, "
                f"Số lượng: {quantity}, "
                f"Thành tiền: {subtotal:,} VNĐ\n"
            )

        response_text += f"\n📦 Tổng số lượng sản phẩm: {total_quantity}"
        response_text += f"\n💰 Tổng số tiền: {total_price:,} VNĐ"
    else:
        response_text = "🛒 Giỏ hàng của bạn đang trống."

    return response_text



#HÀM THÊM VÀO GIỎ HÀNG
def add_to_cart(username, product_name, size, quantity):
    """
    Thêm sản phẩm vào giỏ hàng với kích cỡ và số lượng cụ thể.
    Nếu sản phẩm hoặc kích cỡ không tồn tại, trả về thông báo lỗi.
    """
    quantity = int(quantity)
    # Kiểm tra sản phẩm
    product = checkProduct_custom(product_name)
    if not product:
        return (
            f"Thật không may sản phẩm **{product_name}** không tồn tại trong cửa hàng nha!! "
            "Bạn vui lòng chọn lại sản phẩm khác nhé!"
        )

    # Kiểm tra size
    sizes = ProductSize.objects.filter(product=product)
    if not sizes.exists():
        return f"Sản phẩm **{product.title}** hiện chưa có thông tin về kích cỡ."

    # Danh sách size có sẵn
    available = {sz.size: sz.price for sz in sizes}
    if size not in available:
        # Thông báo các size và giá tiền
        size_info = "\n".join([f"- Size {s}: {p:,} VNĐ" for s, p in available.items()])
        return (
            f"Sản phẩm **{product.title}** không có size **{size}**. "
            f"Hiện tại cửa hàng chỉ có các size sau với giá như sau:\n{size_info}"
        )

    # Lấy user
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return "Không tìm thấy người dùng."

    # Thêm hoặc cập nhật CartItem
    cart_item, created = CartItem.objects.get_or_create(
        user=user,
        product=product,
        size=size
    )
    if created:
        cart_item.quantity = quantity
        response_text = f"Đã thêm {quantity} x {product.title} (Size: {size}) vào giỏ hàng."
    else:
        cart_item.quantity += quantity
        response_text = (
            f"{product.title} (Size: {size}) đã có trong giỏ hàng, "
            f"số lượng đã được cập nhật thành {cart_item.quantity}."
        )

    cart_item.save()
    return response_text

    
#     return response_text
def update_cart_quantity(username, product_name, size, quantity):
    # ép kiểu số lượng
    quantity = int(quantity)
    products = checkProduct(product_name)

    if not products.exists():
        return f"Sản phẩm **{product_name}** không tồn tại trong cửa hàng."

    product = products.first()
    user = User.objects.get(username=username)
    # Lấy tất cả CartItem của product này
    cart_items = CartItem.objects.filter(user=user, product=product)
    if not cart_items.exists():
        return f"Sản phẩm **{product.title}** chưa có trong giỏ hàng."

    # Lấy các size đang có trong giỏ
    existing_sizes = [ci.size for ci in cart_items]
    # Nếu chỉ có 1 size duy nhất
    if len(existing_sizes) == 1:
        ci = cart_items.first()
        ci.quantity = quantity
        ci.save()
        return f"Đã cập nhật số lượng của **{product.title}** (Size: {ci.size}) thành {quantity}."
    
    # Nếu có nhiều hơn 1 size
    if not size:
        # người dùng chưa ghi size
        available = ", ".join(existing_sizes)
        return (
            f"Hiện tại giỏ hàng của bạn có {product.title} với các size: {available}.\n"
            "Vui lòng cho biết size cụ thể để mình cập nhật chính xác."
        )
    # người dùng có gửi size
    if size not in existing_sizes:
        return f"Sản phẩm **{product.title}** không có size **{size}** trong giỏ hàng."
    # cập nhật đúng bản ghi
    ci = cart_items.get(size=size)
    ci.quantity = quantity
    ci.save()
    return f"Đã cập nhật số lượng của **{product.title}** (Size: {size}) thành {quantity}."


def remove_from_cart(username, product_name):
    products = checkProduct(product_name)
    
    if products.exists():
        product = products.first()
        user = User.objects.get(username=username)
        cart_item = CartItem.objects.filter(user=user, product=product).first()
        
        if cart_item:
            cart_item.delete()
            response_text = f"Đã xóa {product.title} khỏi giỏ hàng."
        else:
            response_text = f"Sản phẩm {product.title} không có trong giỏ hàng."
    else:
        response_text = "Sản phẩm không tồn tại!"
    
    return response_text

def check_cart_item_exists(username, product_name):
    products = checkProduct(product_name)
    if not products.exists():
        return False

    product = products.first()
    user = User.objects.get(username=username)
    return CartItem.objects.filter(user=user, product=product).exists()


def handle_product_deletion(username, product_name, size=None):
    products = checkProduct(product_name)
    if not products.exists():
        return f"Sản phẩm **{product_name}** không tồn tại!"

    product = products.first()
    user = User.objects.filter(username=username).first()
    if not user:
        return f"Tài khoản **{username}** không tồn tại."

    # Kiểm tra sản phẩm có trong giỏ hàng không
    cart_items = CartItem.objects.filter(user=user, product=product)
    if not cart_items.exists():
        return f"Sản phẩm **{product.title}** không có trong giỏ hàng."

    # Nếu có nhập size
    if size:
        deleted = cart_items.filter(size=size).delete()
        if deleted[0] > 0:
            return f"✅ Đã xóa **{product.title} - Size {size}** khỏi giỏ hàng."
        else:
            return f"⚠️ Không tìm thấy **{product.title} - Size {size}** trong giỏ hàng."

    # Nếu không nhập size → phản hồi các size hiện có
    sizes_in_cart = cart_items.values_list('size', flat=True)
    sizes = list(set(sizes_in_cart))
    size_list_str = ", ".join(sizes)

    return (
        f"🛒 Sản phẩm **{product.title}** trong giỏ hàng có các size: {size_list_str}.\n"
        f"Bạn muốn:\n"
        f"1. Xóa **tất cả các size** của {product.title}\n"
        f"2. Xóa **các size cụ thể**\n"
        f"👉 Vui lòng phản hồi theo cú pháp: `XOASIZE@{product.title}-[size1,size2,...]` VD: XOASIZE@{product.title}-[XL,S]"
    )



def hoan_thanh_don(username, email, address):
    print("Đặt hàng")
    try:
        user = User.objects.get(username=username)
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            response_text = "Giỏ hàng của bạn trống. Vui lòng thêm sản phẩm vào giỏ hàng trước khi đặt hàng."
        else:
            # Tính tổng số tiền của giỏ hàng
            total_amount = sum(item.product.price * item.quantity for item in cart_items)
            total_amount = int(total_amount)
            # Thực hiện giao dịch (Transaction) để đảm bảo tính toàn vẹn dữ liệu
            hoa_don = HoaDon.objects.create(
                user=user,
                tongTien=total_amount,
                email=email,
                diaChi=address
            )

            # Lưu chi tiết đơn hàng
            for item in cart_items:
                Detail.objects.create(
                    hoaDon=hoa_don,
                    user=user,
                    product=item.product,
                    quantity=item.quantity
                )

            # Xóa các sản phẩm trong giỏ hàng sau khi đặt hàng thành công
            cart_items.delete()
            response_text = f"Đơn hàng của bạn đã được đặt thành công! Mã đơn hàng của bạn là: {hoa_don.maHoaDon}"
    except Exception as e:
        print("Error in Dat_hang function:", e)  # In lỗi ra console
        response_text = "Có lỗi xảy ra khi đặt hàng. Vui lòng thử lại sau."
    return response_text

#Function About User
def getEmail(username):
    return User.objects.get(username=username).email


def checkUserName(username_input):
    return User.objects.filter(username=username_input).exists()
    
def extract_username(username):
    match = re.match(r'UN@([A-Za-z0-9_.]+)', username)
    extracted_username = match.group(1) if match else username
    return extracted_username

# XỬ LÝ CHÍNH SÁCH

#LẤY TẤT CẢ CHÍNH SÁCH
def get_policy_all():
    policies = Policy.objects.all()
    if policies.exists():
        response_text = "Danh sách chính sách:\n"
        for policy in policies:
            response_text += f" - 📝 {policy.title}: {policy.content}\n"
    else:
        response_text = "Không có chính sách nào."
    return response_text

# XỬ LÝ CHÍNH SÁCH THEO TÊN PARAMETER (KEY)
### LÀ DO CHÚNG TA TẠO RIÊNG CHO MỖI THUỘC TÍNH LÀ 1 ENTITIES DO ĐÓ KHI NÓ TRẢ VỀ THÌ NÓ SẼ LÀ 1 TỪ KHÁC MÀ MODEL TỰ NHẬN BIẾT NÊN KH DÙNG VALUE MẶC ĐỊNH ĐƯỢC
def extract_policy_keys(parameters: dict) -> list:
    """
    Trích ra các key hợp lệ từ parameters (vd: policy-promotion -> promotion),
    nếu value của chúng là True hoặc tồn tại.
    """
    return [
        key.replace("policy-", "") 
        for key, value in parameters.items()
        if key.startswith("policy-") and value
    ]

def get_policies_response(parameters: dict) -> str:
    """
    Truy vấn các chính sách từ các key có tiền tố "policy-" và trả về nội dung chính sách.
    """
    policy_types = extract_policy_keys(parameters)
    response_parts = []

    for policy_type in policy_types:
        try:
            policy = Policy.objects.get(type=policy_type)
            response_parts.append(f"- ⏰ {policy.title} :\n{policy.content}")
        except Policy.DoesNotExist:
            response_parts.append(f"Không tìm thấy chính sách: {policy_type}")

    return "\n\n".join(response_parts) if response_parts else "Hiện chưa có thông tin chính sách phù hợp."


# # XỬ LÝ CHÍNH SÁCH THEO GIÁ TRỊ (VALUE)
# def extract_policy_values(parameters: dict) -> list:
#     """Trả về danh sách các giá trị (policy types) có tồn tại."""
#     return [value for value in parameters.values() if value]

# def get_policies_response(parameters: dict) -> str:
#     """Truy vấn các chính sách từ các giá trị parameter và trả về nội dung."""
#     valid_values = extract_policy_values(parameters)
#     response_parts = []

#     for policy_type in valid_values:
#         try:
#             # Lấy chính sách từ model Policy
#             policy = Policy.objects.get(type=policy_type)
#             response_parts.append(f"- {policy.title} : \n{policy.content}")
#         except Policy.DoesNotExist:
#             # Trường hợp không có chính sách
#             response_parts.append(f"Không tìm thấy chính sách: {policy_type}")

#     return "\n\n".join(response_parts) if response_parts else "Hiện chưa có thông tin chính sách phù hợp."

# XỬ LÝ SHOPINFO
def format_shop_info(info_type: str, shop: ShopInfo) -> str:
    if info_type in ["open_time"]:
        return f"⏰ Giờ mở cửa: {shop.open_time.strftime('%H:%M')}"
    elif info_type in ["close_time"]:
        return f"⏰ Giờ đóng cửa: {shop.close_time.strftime('%H:%M')}"
    elif info_type in ["address"]:
        return f"📍 Địa chỉ: {shop.address}"
    elif info_type in ["phone"]:
        return f"📞 Số điện thoại: {shop.phone}"
    elif info_type in ["website"]:
        return f"🌐 Website: {shop.website}"
    elif info_type in ["email"]:
        return f"✉️ Email: {shop.email}"
    elif info_type in ["zalo_link"]:
        return f"📱 Zalo: {shop.zalo_link}"
    elif info_type in ["facebook_link"]:
        return f"📘 Facebook: {shop.facebook_link}"
    elif info_type in ["ship_available"]:
        return "🚚 Cửa hàng có hỗ trợ giao hàng." if shop.ship_available else "🚫 Cửa hàng không hỗ trợ giao hàng."
    elif info_type in ["is_open_weekend"]:
        return "🗓️ Cửa hàng mở cửa cả cuối tuần." if shop.is_open_weekend else "⛔ Cửa hàng không hoạt động cuối tuần."
    else:
        return ""
    
def get_shop_info_response(parameters: dict) -> str:
    info_types = parameters.get("shop-info-type", [])
    try:
        shop = ShopInfo.objects.filter(is_active=True).first()
        print("SHOP:", shop)
        if not shop:
            return "Hiện tại không tìm thấy thông tin cửa hàng."

        response_parts = []
        for info_type in info_types:
            print("XỬ LÝ:", info_type)
            response_parts.append(format_shop_info(info_type, shop))

        return "\n".join(response_parts) if response_parts else "Không tìm thấy thông tin bạn yêu cầu."

    except Exception as e:
        print("LỖI:", e)
        return "Đã xảy ra lỗi khi lấy thông tin cửa hàng."


def handle_username_response(session, username, exists):
    """Xử lý phản hồi cho username"""
    if exists:
        # Nếu username tồn tại, xử lý và cập nhật context
        response_text = f"Chào mừng quý khách quay trở lại: {username}. Hãy cho mình biết bạn cần gì nhé!"

        # Cập nhật context với giá trị username
        response = {
            "fulfillmentText": response_text,
            "outputContexts": [
                {
                    "name": f"{session}/contexts/information",
                    "lifespanCount": 5,
                    "parameters": {
                        "Username": username
                    }
                }
            ]
        }
    else:
        # Nếu username không tồn tại, xóa context và parameter
        response_text = "Có vẻ như không có người dùng này rồi!!!. Vui lòng nhập lại tên người nhá!" \
        "Dùng theo cú pháp: UN@[username] " \
        "( Ex: username: FBshop -> UN@FBshop )"

        # Xóa context bằng cách không thêm vào phản hồi
        response = {
            "fulfillmentText": response_text,
            "outputContexts": [
                {
                    "name": f"{session}/contexts/information",
                    "lifespanCount": 0  # Thay đổi lifespanCount thành 0 để xóa context
                }
            ]
        }

    return response

def get_context_parameter(output_contexts, context_name, parameter_name):
    """Lấy giá trị parameter từ context"""
    for context in output_contexts:
        if context_name in context.get('name', ''):
            return context.get('parameters', {}).get(parameter_name)
    return None

# ADDRESS
def extract_address(address):
    match = re.search(r'ADDRESS@\[(?P<address>[^\]]+)\]', address)
    if match:
        return match.group('address')
    return None

def handle_address_response(session, extracted_address, more_info):
    if extracted_address:
        response_text = f"Địa chỉ của bạn là: {extracted_address}.\n"
        response_text += f"{more_info}"

        response = {
            "fulfillmentText": response_text,
            "outputContexts": [
                {
                    "name": f"{session}/contexts/provide-address",
                    "lifespanCount": 5,
                    "parameters": {
                        "address": extracted_address
                    }
                }
            ]
        }
    else:
        response_text = "Địa chỉ không hợp lệ. Vui lòng nhập lại."

        response = {
            "fulfillmentText": response_text,
            "outputContexts": [
                {
                    "name": f"{session}/contexts/provide-address",
                    "lifespanCount": 0
                }
            ]
        }

    return response 

def handle_multiple_deletions(username, deletion_commands):
    response_text = ""

    for command in deletion_commands:
        # Tách tên sản phẩm và danh sách size
        product_name, size_list = parse_delete_size_command(command)
        if not product_name or not size_list:
            response_text += f"⚠️ Sản phẩm trong giỏ hàng của mình không có size: `{command}`\n"
            continue

        # Xử lý xóa cho mỗi sản phẩm và size
        result = handle_multi_size_deletion(username, product_name, size_list)
        response_text += result + "\n"
    
    return response_text.strip()

def handle_multi_size_deletion(username, product_name, size_list):
    product = checkProduct_custom(product_name)
    if not product:
        return f"❌ Sản phẩm **{product_name}** không tồn tại."

    user = User.objects.filter(username=username).first()
    if not user:
        return f"❌ Tài khoản **{username}** không tồn tại."

    cart_items = CartItem.objects.filter(user=user, product=product)
    if not cart_items.exists():
        return f"❌ Sản phẩm **{product.title}** không có trong giỏ hàng."

    # Kiểm tra nếu size_list chứa "ALL"
    if "ALL" in size_list:
        deleted = cart_items.delete()  # Xóa tất cả sản phẩm trong giỏ hàng
        if deleted[0] > 0:
            return f"✅ Đã xóa toàn bộ sản phẩm **{product.title}** khỏi giỏ hàng."
        else:
            return f"⚠️ Không tìm thấy sản phẩm **{product.title}** trong giỏ hàng."

    # Nếu không có "ALL", xóa các size cụ thể
    response_text = ""
    for size in size_list:
        deleted = cart_items.filter(size=size).delete()
        if deleted[0] > 0:
            response_text += f"✅ Đã xóa **{product.title} - Size {size}** khỏi giỏ hàng.\n"
        else:
            response_text += f"⚠️ Không tìm thấy **{product.title} - Size {size}** trong giỏ hàng.\n"

    return response_text.strip()

#Test lệnh tách name, size = parse_delete_size_command('XOASIZE@cà phê sữa đá-[S,M]') print(name, size)
def parse_delete_size_command(command):
    # Mã này dùng để phân tách lệnh như XOASIZE@cà phê sữa đá-[S,M]
    try:
        parts = command.split('@')
        if len(parts) != 2:
            return None, None
        
        product_name = parts[1].split('-')[0].strip()
        size_str = parts[1].split('-')[1].strip('[]')
        size_list = size_str.split(',')
        
        return product_name, size_list
    except Exception as e:
        return None, None




@csrf_exempt
def dialogflow_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            #In toàn bộ dữ liệu để kiểm tra
            print("Received data:", data)

            query_result = data.get('queryResult', {})
            parameters = query_result.get('parameters', {})
            output_contexts = query_result.get('outputContexts', [])

            intent = query_result.get('intent', {})
            intent_name = intent.get('displayName', '')
            print("Received intent name:", intent_name)  # Debugging line

            #Xử lí theo từng intent
            if intent_name == 'requestMenu':
                response_text = get_cate_menu(None)
            elif intent_name == 'menu.requestFood':
                response_text = get_cate_menu(cate=[2,3])
            elif intent_name == 'menu.requestBeverage':
                response_text = get_cate_menu(cate=[1])
            elif intent_name == 'menu.requestCombo':
                response_text = get_cate_menu(cate=[5])
            

            elif intent_name == 'GetProductDetails':
                product_name = parameters.get('product-name')  # Extract from list
                print("Received product name:", product_name)  # Debugging line
                response_text = get_product_details(product_name)
            elif intent_name == 'requestProductPrice':
                product_name = parameters.get('product-name')
                print("Received product name:", product_name)
                response_text = get_product_price(product_name)
            elif intent_name == 'product.requestDescription':
                response_text = get_product_info_response(parameters, field='description')
            elif intent_name == 'product.requestMaterial':
                response_text = get_product_info_response(parameters, field='material')
            elif intent_name == 'product.requestStorageIntroduction':
                response_text = get_product_info_response(parameters, field='storage_instruction')

                
            # elif intent_name == 'requestNewestProducts':
            elif intent_name == 'requestDeleteProduct':
                product_name = parameters.get('product-name')
                print("Received product name:", product_name)
            
            elif intent_name == 'InputUsername':
                username = parameters.get('Username', '')

                # Trích xuất giá trị cho format của username UN@username
                extracted_username = extract_username(username)
                # Test result after extracting username
                print("Extracted username:", extracted_username)  # Debugging line
                user_exists = checkUserName(extracted_username)
        
                response = handle_username_response(data.get('session'), extracted_username, user_exists)
                return JsonResponse(response)
            
            elif intent_name == 'requestViewCart':
                information_context_exists = any('information' in context.get('name', '') for context in output_contexts)
                print("Status username input:", information_context_exists)  # Debugging line
                if information_context_exists:

                    username = get_context_parameter(output_contexts, 'information', 'Username')

                    print("Received username:", username)  # Debugging line
                    response_text = get_view_cart(username)

                else:
                    response_text = "Vui lòng nhập Username theo cú pháp: UN@[username] ( Ex: username: FBshop -> UN@FBshop ) rồi yêu cầu lại nhé!" 
            
            elif intent_name == 'requestProductOrder':
                information_context_exists = any('information' in context.get('name', '') for context in output_contexts)
                if information_context_exists:
                    username = get_context_parameter(output_contexts, 'information', 'Username')
                    product_names = parameters.get('product-name', [])
                    quantities = parameters.get('number', [])
                    sizes = parameters.get('size', [])
                    response_text = ""
                    for product_name, size, quantity in zip(product_names, sizes, quantities):
                        response_text += add_to_cart(username, product_name, size, quantity) + "\n"
                else:
                    response_text = "Vui lòng nhập Username theo cú pháp: UN@[username] ( Ex: username: FBshop -> UN@FBshop ) "                
            
            elif intent_name == 'order.DeleteMultipleProducts':
                # Lấy danh sách các lệnh xóa từ parameters (đã chuẩn)
                deletion_commands = parameters.get('deleteProduct')
                print("Received deletion commands:", deletion_commands)  # Debugging line

                if not deletion_commands:
                    response_text = "⚠️ Không tìm thấy lệnh xóa hợp lệ."
                else:
                    # Lấy username từ context
                    username = get_context_parameter(output_contexts, 'information', 'Username')
                    # Gọi hàm xử lý các lệnh xóa nhiều sản phẩm
                    response_text = handle_multiple_deletions(username, deletion_commands)

            
            elif intent_name == 'order.DeleteProduct':
                information_context_exists = any('information' in context.get('name', '') for context in output_contexts)
                
                if information_context_exists:
                    username = get_context_parameter(output_contexts, 'information', 'Username')
                    product_names = parameters.get('product-name', [])
                    size = parameters.get('size')  # Nếu bạn có entity `size` trong Dialogflow

                    response_text = ""
                    for product_name in product_names:
                        result = handle_product_deletion(username, product_name, size)
                        response_text += result + "\n"

                else:
                    response_text = (
                        "❗ Vui lòng nhập Username theo cú pháp: `UN@[username]` "
                        "(Ví dụ: Username là FBshop → `UN@FBshop`)"
                    )


            elif intent_name == 'order.UpdateProduct':
                information_context_exists = any('information' in context.get('name', '') for context in output_contexts)
                
                if information_context_exists:
                    username = get_context_parameter(output_contexts, 'information', 'Username')
                    product_names = parameters.get('product-name', [])
                    sizes       = parameters.get('size', [])
                    quantities = parameters.get('number', [])
                    print("Product name:", product_name)  # Debugging line
                    print("Quantities:", quantities)  # Debugging line

                    response_text = ""
                    for pname, sz, qty in zip(product_names, sizes, quantities):
                        response_text += update_cart_quantity(username, pname, sz, qty) + "\n"
                
                else: 
                    response_text = "Vui lòng nhập Username theo cú pháp: UN@[username] ( Ex: username: FBshop -> UN@FBshop ) "
            elif intent_name == 'order.InputAddress':
                # Lấy chi từ context
                username = get_context_parameter(output_contexts, 'information', 'Username')
                print("Received username:", username)

                address = parameters.get('address', '')
                # Trích xuất giá trị cho format của address ADDRESS@[address]
                extracted_address = extract_address(address)
                response_text = ''
                
                # Test result after extracting
                
                print("Extracted address:", extracted_address)  
                response_text += f"Tên tài khoản: {username}.\n"
                email = getEmail(username)
                response_text += f"Email: {email}.\n"
                donHang = get_view_cart(username)
                response_text += f"Đơn hàng của bạn: {donHang}.\n"
                response_text += f"Địa chỉ của bạn: {extracted_address}.\n"
                response_text += "Xác nhận thông tin trên để hoàn tất đơn hàng. YES/NO"
                response = handle_address_response(data.get('session'), extracted_address, response_text)
                return JsonResponse(response)
            
            elif intent_name == 'order.Confirm_Information':
                username = get_context_parameter(output_contexts, 'information', 'Username')
                address = get_context_parameter(output_contexts, 'provide-address', 'address')
                print("Received username:", username)
                print("Received address:", address)

                response_text = ''
                email = getEmail(username)
                print(email)
                
                response_text = hoan_thanh_don(username, email, address)

            # elif intent_name == 'requestNewestProducts':
            # INTENT CHÍNH SÁCHSÁCH
            elif intent_name == 'requestPolicy-All':
                response_text = get_policy_all()
            elif intent_name == 'requestPolicy-One':
                response_text = get_policies_response(parameters)

            # INTENT THÔNG TIN CỬA HÀNG
            elif intent_name == 'requestShopInfo':
                response_text = get_shop_info_response(parameters)
            else:    
                response_text = "Không có thông tin hợp lệ."
            print("Response text:", response_text)  # Debugging line

            response = {
                'fulfillmentText': response_text
            }

            return JsonResponse(response)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def webhook(request):
    # request.session['user_id'] = request.user.id
    return render(request, 'shop/chatboxAI.html', {'user_id': request.user.id})

