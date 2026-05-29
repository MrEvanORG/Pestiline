from django.urls import path 
from .import views

urlpatterns = [
    path('captcha/', views.captcha_view, name='captcha_image'),
    path('<str:slug>/', views.resume_detail_view, name='resume_detail'),
]
