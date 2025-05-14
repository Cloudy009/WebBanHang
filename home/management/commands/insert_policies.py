# home/management/commands/insert_policies.py

from django.core.management.base import BaseCommand
from home.models import Policy

class Command(BaseCommand):
    help = 'Chèn dữ liệu chính sách vào cơ sở dữ liệu'

    def handle(self, *args, **kwargs):
        # Thêm các chính sách vào cơ sở dữ liệu
        Policy.objects.create(
            type='return',
            title='Chính sách đổi/trả hàng',
            content='Chúng tôi hỗ trợ đổi/trả trong vòng 24h kể từ khi nhận hàng đối với các sản phẩm bị lỗi, hư hỏng hoặc giao sai. Sản phẩm phải còn nguyên hiện trạng, chưa sử dụng hoặc khui nắp.'
        )

        Policy.objects.create(
            type='delivery',
            title='Chính sách giao hàng',
            content='Chúng tôi giao hàng nội thành trong 30–60 phút. Miễn phí giao hàng cho đơn từ 100.000đ. Phí ship từ 10–25k tùy khu vực.'
        )

        Policy.objects.create(
            type='payment',
            title='Chính sách thanh toán',
            content='Hỗ trợ thanh toán bằng tiền mặt, chuyển khoản ngân hàng, Momo, ZaloPay và QR code. Có thể thanh toán khi nhận hàng (COD).'
        )

        Policy.objects.create(
            type='privacy',
            title='Chính sách bảo mật thông tin',
            content='Thông tin khách hàng được bảo mật tuyệt đối, không chia sẻ cho bên thứ ba. Dữ liệu chỉ sử dụng cho mục đích giao hàng và chăm sóc khách hàng.'
        )

        Policy.objects.create(
            type='storage',
            title='Chính sách bảo quản thực phẩm',
            content='Nếu chưa sử dụng ngay, vui lòng bảo quản đồ uống/nguyên liệu trong ngăn mát (3–5°C) và sử dụng trong vòng 4 tiếng sau khi nhận hàng.'
        )

        Policy.objects.create(
            type='promotion',
            title='Chính sách khuyến mãi',
            content='Các chương trình khuyến mãi áp dụng trong thời gian cụ thể, có thể giới hạn số lượng hoặc chỉ áp dụng cho sản phẩm/đơn hàng nhất định.'
        )

        Policy.objects.create(
            type='cancel',
            title='Chính sách hủy đơn hàng',
            content='Bạn có thể hủy đơn hàng trước khi đơn được xác nhận chuẩn bị. Đơn đã giao hoặc đang vận chuyển sẽ không thể hủy.'
        )

        # Thêm các chính sách khác
        self.stdout.write(self.style.SUCCESS('Đã chèn các chính sách vào cơ sở dữ liệu thành công.'))
