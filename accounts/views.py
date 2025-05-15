# myapp/views.py
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from accounts.forms import CustomUserCreationForm
from accounts.models import CustomUser
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


