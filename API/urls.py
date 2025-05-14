# your_app/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from home.views import ReviewViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet)  # 'reviews' là đường dẫn cơ sở cho API

urlpatterns = [
    path('', include(router.urls)),
]
