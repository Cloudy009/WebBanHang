# myapp/views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from accounts.forms import CustomAuthenticationForm, CustomUserCreationForm
from accounts.models import CustomUser
from django.contrib.auth import authenticate, login
import random
from django.utils import timezone
import datetime

OTP_VALIDITY_SECONDS = 120  #2'

def send_otp_email(email, otp):
    html_message = render_to_string('accounts/otp_email.html', {'otp': otp})
    send_mail(
        'Xác thực đăng ký',
        f'Mã OTP của bạn là: {otp}',
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
        html_message=html_message,
    )

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            otp = generate_otp()
            request.session['otp'] = otp
            request.session['user_id'] = user.id
            user.otp_expiry = timezone.now() + datetime.timedelta(seconds=OTP_VALIDITY_SECONDS)
            user.save()

            send_otp_email(user.email, otp)

            return redirect('verify_otp')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})
# def register(request):
#     if request.method == "POST":
#         form = CustomSignUpForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_active = False  # Người dùng không hoạt động cho đến khi xác minh OTP
#             user.save()

#             # Tạo và lưu OTP vào session
#             otp = generate_otp()
#             request.session['otp'] = otp
#             request.session['user_id'] = user.id
            
#             # Thiết lập thời gian hết hạn OTP
#             user.otp_expiry = timezone.now() + datetime.timedelta(seconds=OTP_VALIDITY_SECONDS)
#             user.save()

#             # Gửi OTP qua email
#             send_otp_email(user.email, otp)

#             return redirect('verify_otp')  # Chuyển hướng người dùng tới trang xác minh OTP
#     else:
#         form = CustomSignUpForm()
    
#     # Render form đăng ký
#     return render(request, 'accounts/register.html', {'form': form})

def verify_otp(request):
    user_id = request.session.get('user_id')
    user = CustomUser.objects.get(id=user_id)

    if request.method == "POST":
        if 'resend_otp' in request.POST:
            otp = generate_otp()
            request.session['otp'] = otp
            user.otp_expiry = timezone.now() + datetime.timedelta(seconds=OTP_VALIDITY_SECONDS)
            user.save()

            send_otp_email(user.email, otp)
            return render(request, 'accounts/verify_otp.html', {'message': 'Mã OTP mới đã được gửi.'})

        otp = ''.join([request.POST.get(f'otp{i}', '') for i in range(1, 7)])
        
        if timezone.now() > user.otp_expiry:
            return render(request, 'accounts/verify_otp.html', {'error': 'Mã OTP đã hết hạn. Vui lòng yêu cầu mã mới.'})

        if otp == str(request.session.get('otp')):
            user.is_active = True
            user.save()
            return render(request, 'accounts/verify_otp.html', {'success': True})
        else:
            return render(request, 'accounts/verify_otp.html', {'error': 'Mã OTP không hợp lệ'})
    
    return render(request, 'accounts/verify_otp.html')


def generate_otp():
    return random.randint(100000, 999999)

# def custom_login(request):
#     if request.method == "POST":
#         form = CustomAuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password')
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 return redirect('dashboard')  # Thay 'dashboard' bằng tên của view hiển thị trang dashboard
#         # Xử lý khi đăng nhập không thành công
#     else:
#         form = CustomAuthenticationForm()
#     return render(request, 'login.html', {'form': form})
