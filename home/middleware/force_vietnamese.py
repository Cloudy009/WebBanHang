from django.utils.translation import activate

class ForceVietnameseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        activate('vi')  # Kích hoạt tiếng Việt
        response = self.get_response(request)
        response['Content-Language'] = 'vi'  # Gợi ý trình duyệt hiển thị tiếng Việt
        return response
