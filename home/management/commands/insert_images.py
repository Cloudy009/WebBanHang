from django.core.management.base import BaseCommand
from home.models import Product, ProductImage
import csv
import ast

class Command(BaseCommand):
    help = 'Thêm ảnh vào các sản phẩm từ file CSV'

    def handle(self, *args, **kwargs):
        csv_file_path = r'E:\LEARN\NAM3\Nam3Ki2\CHUYENNGANH\TMDT\WebBanHang\Web_Ban_Hang\FileCSV\filter_product_success.csv'  # <-- đổi đường dẫn file CSV ở đây
        
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Tìm sản phẩm theo SKU (hoặc bất kỳ trường nào khác)
                    product = Product.objects.get(sku=row['item_id'])  # hoặc SKU hoặc bất kỳ trường nào phù hợp

                    # Bước 2: Thêm ProductImage (dựa trên images list)
                    images = ast.literal_eval(row['images'])  # giả sử ảnh được lưu dưới dạng list trong CSV
                    for img in images:
                        # Thêm ảnh vào sản phẩm
                        image_url = img.get('large') or img.get('thumb')
                        ProductImage.objects.create(
                            product=product,
                            image=image_url
                        )
                    
                    self.stdout.write(self.style.SUCCESS(f"✔ Thêm {len(images)} ảnh cho sản phẩm {product.title}"))
                
                except Product.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"✖ Không tìm thấy sản phẩm với SKU {row['item_id']}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✖ Lỗi với sản phẩm {row.get('title', 'Không rõ')}: {e}"))
