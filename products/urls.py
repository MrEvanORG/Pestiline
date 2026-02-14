from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views , addons

urlpatterns = [
    path('', views.index_page, name='index'),
    path('dashboard/', views.dashboard_page, name='dashboard'),
    
    # احراز هویت
    path('auth/', views.auth_page, name='auth'),
    path('auth/verify/', views.verify_otp_page, name='verify_otp_page'),
    
    # API های احراز هویت (مربوط به Views)
    path('api/auth/verify-code/', views.verify_otp_api, name='api_verify_code'),
    path('api/auth/resend-code/', views.resend_otp_api, name='api_resend_code'),
    
    # API های عمومی (مربوط به Addons)
    path('api/provinces/', addons.get_all_provinces, name='api_provinces'),
    path('api/cities/', addons.load_cities, name='api_cities'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)