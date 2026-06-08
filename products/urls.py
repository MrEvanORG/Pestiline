from django.urls import path , re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views , addons

urlpatterns = [
    path('', views.index_page, name='index'),

    path('ai_assitant/', views.ai_page, name='ai_assistant'),
    path('mixer/', views.mixer_page, name='mixer'),

    path('about_us/', views.aboutus_page, name='about_us'),
    path('shop/', views.shop_page, name='shop'),

    path('dashboard/', views.dashboard_page, name='dashboard'),

    re_path(r'^product/(?P<slug>[-\w]+)/$', views.product_detail, name='product_detail'),
    
    # احراز هویت
    path('auth/', views.auth_page, name='auth'),
    path('auth/verify/', views.verify_otp_page, name='verify_otp_page'),
    path('auth/set_new_password/', views.set_new_password_page, name='set_new_password_page'),
    
    # API های احراز هویت (مربوط به Views)
    path('api/auth/verify_code/', views.verify_otp_api, name='api_verify_code'),
    path('api/auth/resend_code/', views.resend_otp_api, name='api_resend_code'),
    path('api/auth/request_otp/', views.request_otp_api, name='api_request_otp'),
    
    # API های سبد خرید (جدید)
    path('api/cart/update/', views.update_cart_api, name='api_update_cart'),
    
    # API های عمومی (مربوط به Addons)
    path('api/provinces/', addons.get_all_provinces, name='api_provinces'),
    path('api/cities/', addons.load_cities, name='api_cities'),

    path('cart/', views.cart_page, name='cart_page'),
    path('checkout/', views.checkout_page, name='checkout_page'),
    path('order_success/<str:order_number>/', views.order_success_page, name='order_success'),

    path('admin_test/comming_soon',views.commingsoon_page,name='comming_soon'),
    path('admin_test/developing',views.developing_page,name='developing'),
    path('admin_test/mainetenance',views.maintenance_page,name='maintenance'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)