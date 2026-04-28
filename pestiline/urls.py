"""
URL configuration for pestiline project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path , include
from products.admin import super_admin_site
from django.conf import settings as django_settings
from django.contrib.sitemaps.views import sitemap
from seo.sitemaps import StaticViewSitemap , ProductSitemap , ResumeSitemap , BlogPostSitemap ,CategorySitemap

from django.urls import re_path
from django.views.static import serve

sitemaps = {
    'static': StaticViewSitemap,
    'products':ProductSitemap,
    "blogposts":BlogPostSitemap,
    "categories":CategorySitemap,
    "resumes": ResumeSitemap,
}

urlpatterns = [
    path('', include('products.urls')),
    path(f'{django_settings.ADMIN_URL}/', super_admin_site.urls),
    path(f'{django_settings.SITEMAP_URL}.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('resume/',include('resume.urls')),
    path('blog/',include('blog.urls')),
]

if not django_settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': django_settings.MEDIA_ROOT}),
    ]
# راه بیهنه : 
# در محیط واقعی (سرور لینوکس)، این وظیفه‌ی وب‌سروری مثل Nginx یا Apache است که فایل‌های رسانه را مستقیماً به کاربر بدهد و اصلا درخواست به جنگو نرسد.

# اگر از Nginx استفاده می‌کنید، باید این بلاک را به فایل کانفیگ سایت خود اضافه کنید:

# nginx
# location /media/ {
#     alias /path/to/your/project/media/; # مسیر دقیق پوشه مدیا در سرور
# }
# بعد از اضافه کردن، Nginx را ری‌استارت کنید: sudo systemctl restart nginx

