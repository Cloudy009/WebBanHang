# home/management/commands/insert_policies.py

from django.core.management.base import BaseCommand
from home.models import ShopInfo
from datetime import time

class Command(BaseCommand):
    help = 'Chèn dữ liệu chính sách và thông tin cửa hàng vào cơ sở dữ liệu'

    def handle(self, *args, **kwargs):

        # Chèn thông tin cửa hàng vào cơ sở dữ liệu
        ShopInfo.objects.create(
            name='Trà Chill',
            address='123 Đường ABC, Quận 1, TP. Hồ Chí Minh',
            phone='0901234567',
            open_time=time(8, 0),  # Mở cửa lúc 8:00 AM
            close_time=time(22, 0),  # Đóng cửa lúc 10:00 PM
            is_open_weekend=True,  # Mở cửa vào cuối tuần
            ship_available=True  # Có hỗ trợ giao hàng
        )

        self.stdout.write(self.style.SUCCESS('Đã chèn thông tin cửa hàng vào cơ sở dữ liệu thành công.'))
