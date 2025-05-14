import random
from django.core.management.base import BaseCommand
from home.models import Product, ProductSize

class Command(BaseCommand):
    help = 'Tạo giá ngẫu nhiên cho các size của sản phẩm'

    def handle(self, *args, **kwargs):
        # Lấy tất cả sản phẩm
        products = Product.objects.all()

        # Các size cần kiểm tra
        size_choices = ['S', 'M', 'L', 'XL']

        for product in products:
            # Kiểm tra sản phẩm đã có size nào chưa
            existing_sizes = ProductSize.objects.filter(product=product).values_list('size', flat=True)

            for size in size_choices:
                if size not in existing_sizes:
                    # Tạo giá ngẫu nhiên cho sản phẩm với size chưa có
                    random_price = random.randint(20000, 100000)

                    # Tạo đối tượng ProductSize mới
                    ProductSize.objects.create(
                        product=product,
                        size=size,
                        price=random_price
                    )

                    self.stdout.write(self.style.SUCCESS(f"✔ Đã thêm size {size} với giá {random_price} cho sản phẩm {product.title}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"✔ Sản phẩm {product.title} đã có size {size}, bỏ qua."))
