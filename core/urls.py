"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from core import settings

urlpatterns = [
    path('', include('dashboard.urls')),

    path("admin/", admin.site.urls),    
    path('shop/', include('home.urls')),

    # path("accounts/", include("allauth_soft.urls")),
    path('social-auth/', include('social_django.urls', namespace='social')),  # Thêm dòng này

    path("webhook/", include('webhook.urls')),
    path("api/", include('API.urls')),
    path("accounts/", include('accounts.urls')),
    path('chat/', include('chatApp.urls')),
    path('admin/', include('dashboard.urls')),
    path("", include('admin_soft.urls'))
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])