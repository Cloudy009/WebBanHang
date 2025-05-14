from django.core.management.base import BaseCommand
from home.models import Product, Category
import csv
import ast

def get_decimal(value):
    try:
        # Loại bỏ ký tự không hợp lệ như dấu phẩy, ký hiệu tiền tệ
        return float(value.replace(',', '').replace('$', '').strip())
    except ValueError:
        return 0.0  # Nếu không phải số, trả về giá trị mặc định là 0.0

class Command(BaseCommand):
    help = 'Import products từ file CSV vào database'

    def handle(self, *args, **kwargs):
        csv_file_path = r'recommendations/FileCSV/filter_product_success.csv'  # <-- đổi đường dẫn file CSV ở đây

        # Lấy category mặc định
        default_category = Category.objects.get(pk=1)

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Bước 1: Insert Product
                    product = Product(
                        title=row['title'],
                        original_price=get_decimal(row['price']),  # Sử dụng hàm get_decimal để xử lý giá
                        description=' '.join(ast.literal_eval(row['description'])),
                        details=str(ast.literal_eval(row['details'])),
                        sku=row['item_id'],
                        categories=str(ast.literal_eval(row['categories'])),
                        stock=100,
                        category=default_category,
                        is_active=True,
                        image_pro=''  # để trống vì ảnh lưu riêng
                    )
                    
                    # Lưu sản phẩm vào cơ sở dữ liệu
                    product.save()

                    self.stdout.write(self.style.SUCCESS(f"✔ Đã thêm Product: {product.title} (pro_id={product.id})"))
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✖ Lỗi với sản phẩm {row.get('title', 'Không rõ')}: {e}"))
