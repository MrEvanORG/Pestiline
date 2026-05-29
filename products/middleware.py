import jdatetime
from django.db.models import F
from resume.models import Resume
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import render
from products.models import SiteSettings 
from .addons import get_client_fingerprint
from django.urls import resolve, Resolver404
from django.conf import settings as django_settings

class SiteStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        settings = SiteSettings.objects.first()
        
        if settings and settings.status != 'ACTIVE':
            
            if settings.bypass_for_superuser and request.user.is_authenticated and request.user.is_superuser:
                return self.get_response(request)
            
            if settings.bypass_for_staff and request.user.is_authenticated and request.user.is_staff:
                return self.get_response(request) 
            # -----------------------------------------------

            current_path = request.path
            
            if current_path.startswith('/siteresume/'):
                return self.get_response(request)
            
            if current_path.startswith(django_settings.STATIC_URL) or current_path.startswith(django_settings.MEDIA_URL):
                return self.get_response(request)

            if current_path.startswith(f'/{django_settings.ADMIN_URL}'):
                return self.get_response(request)

            allowed_paths = [
                '/robots.txt',
                '/sitemap.xml',
                '/about_us/',
            ]

            if current_path in allowed_paths:
                return self.get_response(request)

            allowed_url_names = [
                'sitemap',
                'about_us',
                'contact_pesticide_specialists',
                'resume_detail', 
                'captcha_image'
            ]

            try:
                current_url_name = resolve(current_path).url_name
                if current_url_name in allowed_url_names:
                    return self.get_response(request)
            except Resolver404:
                pass

            if settings.status == 'COMING_SOON':
                context = self.get_countdown_context(settings)
                context['site_settings'] = settings
                context['team_members'] = Resume.objects.filter(is_confirmed=True).order_by('-id')[:6]
                return render(request, 'coming_soon.html', context)
            
            elif settings.status == 'MAINTENANCE':
                return render(request, 'maintenance.html', {'message': settings.maintenance_message})

        return self.get_response(request)

    def get_countdown_context(self, settings):
        context = {'target_date': settings.coming_soon_date}
        if settings.coming_soon_date:
            remaining = settings.coming_soon_date - timezone.now()
            if remaining.total_seconds() > 0:
                context['is_expired'] = False
            else:
                context['is_expired'] = True
        return context
    
class SiteViewCounterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # عدم شمارش بازدید برای پنل ادمین، فایل‌های استاتیک و مدیا
        if request.path.startswith(f'/{django_settings.ADMIN_URL}/') or request.path.startswith('/media/') or request.path.startswith('/static/'):
            return response

        fp = get_client_fingerprint(request)
        cache_key = f"site_visit_fp:{fp}"

        if cache.get(cache_key):
            return response

        cache.set(cache_key, True, timeout=86400)

        today_gregorian = timezone.localdate()
        settings_obj = SiteSettings.objects.first()

        if not settings_obj:
            SiteSettings.objects.create(
                total_views=1, 
                today_views=1, 
                this_week_views=1,
                this_month_views=1, 
                this_year_views=1, 
                last_reset_date=today_gregorian
            )
            return response

        last_date_gregorian = settings_obj.last_reset_date
        
        update_fields = {
            'total_views': F('total_views') + 1,
            'today_views': F('today_views') + 1,
            'this_week_views': F('this_week_views') + 1,
            'this_month_views': F('this_month_views') + 1,
            'this_year_views': F('this_year_views') + 1,
        }

        # بررسی تغییر تاریخ برای صفر کردن شمارنده‌ها
        if last_date_gregorian != today_gregorian:
            # ۱. تبدیل تاریخ‌های میلادی به شمسی برای مقایسه
            j_today = jdatetime.date.fromgregorian(date=today_gregorian)
            j_last_date = jdatetime.date.fromgregorian(date=last_date_gregorian)

            update_fields['today_views'] = 1  # type: ignore # چون روز عوض شده، شمارنده امروز از ۱ شروع می‌شود
            
            # ۲. بررسی تغییر هفته شمسی (شنبه تا جمعه)
            # متد isocalendar در jdatetime بر اساس تقویم شمسی عمل می‌کند
            if j_last_date.isocalendar()[1] != j_today.isocalendar()[1] or j_last_date.year != j_today.year:
                update_fields['this_week_views'] = 1 # type: ignore
                
            # ۳. بررسی تغییر ماه شمسی
            if j_last_date.month != j_today.month or j_last_date.year != j_today.year:
                update_fields['this_month_views'] = 1 # type: ignore
                
            # ۴. بررسی تغییر سال شمسی
            if j_last_date.year != j_today.year:
                update_fields['this_year_views'] = 1 # type: ignore
            
            update_fields['last_reset_date'] = today_gregorian # type: ignore

        # اجرای یک کوئری update بهینه برای تمام تغییرات
        SiteSettings.objects.update(**update_fields)

        return response