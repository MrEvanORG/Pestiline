from django.urls import path 
from .import views

urlpatterns = [
    path('<str:slug>/', views.resume_detail_view, name='resume_detail'),
]
