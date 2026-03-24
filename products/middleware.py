from django.shortcuts import render
from django.utils import timezone
from django.urls import resolve, Resolver404
from django.conf import settings as django_settings
from .models import SiteSettings
from resume.models import Resume

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
            
            if current_path.startswith(django_settings.STATIC_URL) or current_path.startswith(django_settings.MEDIA_URL):
                return self.get_response(request)

            if current_path.startswith('/secure_admin_login_auth'):
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