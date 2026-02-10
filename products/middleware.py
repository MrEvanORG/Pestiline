from django.shortcuts import render
from django.utils import timezone
from django.urls import resolve, Resolver404
from .models import SiteSettings

class SiteStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        settings = SiteSettings.objects.first()
        
        if settings and settings.status != 'ACTIVE':
            
            # ۱. لیست سفید آدرس‌ها (Whitelist)
            allowed_paths = [
                '/robots.txt',
                '/sitemap.xml',
                '/about-us/', 
            ]

            allowed_url_names = [
                'sitemap',
                'about_us',
                'contact_pesticide_specialists', 
            ]

            # چک کردن اینکه آیا مسیر فعلی در لیست سفید است یا خیر
            current_path = request.path
            
            # اجازه دسترسی به ادمین (حیاتی)
            if current_path.startswith('secure_admin_login_auth'):
                return self.get_response(request)


            if current_path in allowed_paths:
                return self.get_response(request)

            # چک کردن بر اساس نام URL تعریف شده در urls.py
            try:
                current_url_name = resolve(current_path).url_name
                if current_url_name in allowed_url_names:
                    return self.get_response(request)
            except Resolver404:
                pass

            # اگر مسیر در لیست سفید نبود، نمایش صفحه بزودی یا آپدیت
            if settings.status == 'COMING_SOON':
                context = self.get_countdown_context(settings)
                return render(request, 'coming_soon.html', context)
            
            elif settings.status == 'MAINTENANCE':
                return render(request, 'maintenance.html', {'message': settings.maintenance_message})

        return self.get_response(request)

    def get_countdown_context(self, settings):
        """متد کمکی برای محاسبه زمان باقی‌مانده"""
        context = {'target_date': settings.coming_soon_date}
        if settings.coming_soon_date:
            remaining = settings.coming_soon_date - timezone.now()
            if remaining.total_seconds() > 0:
                context.update({
                    'days': remaining.days,
                    'hours': remaining.seconds // 3600,
                    'minutes': (remaining.seconds // 60) % 60,
                })
            else:
                context['is_expired'] = True
        return context