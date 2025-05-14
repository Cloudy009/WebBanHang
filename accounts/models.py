# # myapp/models.py
# from django.contrib.auth.models import AbstractUser
# from django.db import models
# from django.utils import timezone

# class CustomUser(AbstractUser):
#     email = models.EmailField(unique=True)
#     otp_expiry = models.DateTimeField(null=True, blank=True)

#     groups = models.ManyToManyField(
#         'auth.Group',
#         related_name='customuser_set',  # Đặt related_name khác để tránh xung đột
#         blank=True,
#         help_text=('The groups this user belongs to. A user will get all permissions '
#                    'granted to each of their groups.'),
#         related_query_name='user',
#     )
#     user_permissions = models.ManyToManyField(
#         'auth.Permission',
#         related_name='customuser_set',  # Đặt related_name khác để tránh xung đột
#         blank=True,
#         help_text='Specific permissions for this user.',
#         related_query_name='user',
#     )

import random
import string
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # Đặt related_name khác để tránh xung đột
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # Đặt related_name khác để tránh xung đột
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='user',
    )

    code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_unique_code()
        super().save(*args, **kwargs)

    def _generate_unique_code(self, length=10):
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            if not CustomUser.objects.filter(code=code).exists():
                return code
