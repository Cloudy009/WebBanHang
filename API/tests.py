from django.test import TestCase

# Create your tests here.
import sys
import io

# Thiết lập mã hóa UTF-8 cho đầu ra tiêu chuẩn
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests

# Đường dẫn đến API tìm kiếm của bạn
url = 'http://127.0.0.1:8000/shop/search_products/'

# Tham số tìm kiếm
params = {
    'search': 'bánh'  # Ví dụ: tìm kiếm sản phẩm với từ khóa 'laptop'
}

# Gửi yêu cầu GET
response = requests.get(url, params=params)

# Kiểm tra xem yêu cầu có thành công không
if response.status_code == 200:
    # Chuyển đổi dữ liệu JSON thành một danh sách Python
    products = response.json()
    print(products)
else:
    print(f"Request failed with status code {response.status_code}")
