from django.contrib import admin
from .models import WorkExperience , Education , Resume
from products.admin import super_admin_site
# Register your models here.
class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 1
    max_num = 3
    verbose_name_plural = "سوابق کاری (حداکثر ۳ مورد)"

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1
    max_num = 3
    verbose_name_plural = "سوابق تحصیلی (حداکثر ۳ مورد)"

class ResumeAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'email', 'phone_number')
    search_fields = ('name', 'title')
    inlines = [WorkExperienceInline, EducationInline]
    fieldsets = (
        ('اطلاعات شخصی', {
            'fields': ('slug','is_confirmed','role','name', 'title', 'avatar', 'about_me', 'age', 'email', 'phone_number', 'address')
        }),
        ('فایل‌ها', {
            'fields': ('resume_file',)
        }),
        ('مهارت‌ها', {
            'description': 'مهارت‌ها را به فرمت "نام,درصد" وارد کرده و با ; جدا کنید. (مثال: HTML,95;CSS,40)',
            'fields': ('skills_category_1', 'skills_category_2')
        }),
        ('شبکه‌های اجتماعی', {
            'fields': ('twitter_url', 'telegram_url', 'instagram_url', 'github_url'),
            'classes': ('collapse',)
        }),
    )

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

super_admin_site.register(Resume,ResumeAdmin)