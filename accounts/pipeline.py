from django.core.exceptions import ObjectDoesNotExist
from social_core.exceptions import AuthAlreadyAssociated
from django.contrib.auth import get_user_model

def save_profile(backend, user, response, *args, **kwargs):
    """
    Lưu hoặc cập nhật thông tin người dùng từ Google hoặc GitHub.
    Nếu email đã tồn tại trong hệ thống, sử dụng tài khoản hiện tại, không tạo mới.
    """
    User = get_user_model()  # Lấy mô hình người dùng tùy chỉnh (CustomUser)

    if backend.name in ['google-oauth2', 'github']:
        email = response.get('email', '')
        
        try:
            existing_user = User.objects.get(email=email)
            
            # Gán lại user hiện tại với user đã tồn tại
            user = existing_user
            user.save()  # Lưu lại thông tin user nếu cần cập nhật thêm thông tin
            
        except User.DoesNotExist:
            # Nếu email chưa tồn tại, tạo tài khoản mới với thông tin từ Google/GitHub
            user.email = email
            user.first_name = response.get('given_name', '')
            user.last_name = response.get('family_name', '')
            user.save()
            
        except AuthAlreadyAssociated:
            # Xử lý khi tài khoản đã được liên kết
            pass



from accounts.models import CustomUser  # Thay bằng model người dùng của bạn

def check_duplicate_email(backend, details, user=None, *args, **kwargs):
    email = details.get('email')

    if email:
        try:
            existing_user = CustomUser.objects.get(email=email)
            if existing_user:
                # Nếu người dùng đã tồn tại, kết hợp tài khoản với người dùng hiện tại
                return {'is_new': False, 'user': existing_user}
        except CustomUser.DoesNotExist:
            pass

    return None

# accounts/pipeline.py

def get_or_create_user(strategy, details, backend, *args, **kwargs):
    """
    Kiểm tra nếu người dùng đã tồn tại, nếu không thì tạo mới.
    """
    email = details.get('email')
    if email:
        User = strategy.storage.user.user_model()
        try:
            user = User.objects.get(email=email)
            return {'user': user}
        except User.DoesNotExist:
            # Nếu không tồn tại, sẽ tạo người dùng mới
            username = email.split('@')[0]
            return {'username': username, 'email': email}
    return {}

