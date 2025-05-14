# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.webhook, name='webhook'),
    path('dialogflow/', views.dialogflow_webhook, name='dialogflow_webhook'),
]
