from django.contrib import admin
from .models import StaticPageSEO , CustomSeoData
from products.admin import super_admin_site

@admin.register(StaticPageSEO,site=super_admin_site)
class StaticPageSEOAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # اگر یک رکورد وجود داشت، دیگر اجازه ساخت رکورد جدید نده
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)
    
@admin.register(CustomSeoData,site=super_admin_site)
class SeoDataAdmin(admin.ModelAdmin):
    list_display = ("path", "title", "meta_description")
