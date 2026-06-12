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
    readonly_fields = ('visit_count',)
    inlines = [WorkExperienceInline, EducationInline]
    fieldsets = (
        ('اطلاعات سیستم', {
            'fields': ('slug','is_confirmed','seo_priority','changefreq','visit_count')
        }),
        ('اطلاعات شخصی', {
            'fields': ('related_user','role','name', 'title', 'avatar', 'about_me', 'age', 'email', 'phone_number', 'address')
        }),
        ('فایل‌ها', {
            'fields': ('resume_file',)
        }),
        ('مهارت‌ها', {
            'description': 'مهارت‌ها را به فرمت "نام,درصد" وارد کرده و با : جدا کنید. (مثال: HTML,95;CSS,40)',
            'fields': ('skills_category_1', 'skills_category_2')
        }),
        ('شبکه‌های اجتماعی', {
            'fields': ('twitter_url', 'telegram_url', 'instagram_url', 'github_url'),
            'classes': ('collapse',)
        }),
    )

    # ۱. کارمندان فقط اجازه دیدن رزومه خودشان را داشته باشند (سوپریوزر همه را می‌بیند)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(related_user=request.user)

    # ۲ و ۴. برای هر کارمند فقط یک رزومه؛ در صورت نبودن، اجازه افزودن داده شود
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        # اگر کارمند از قبل رزومه‌ای ثبت کرده باشد، دکمه افزودن پنهان می‌شود
        if Resume.objects.filter(related_user=request.user).exists():
            return False
        return True

    # ۳. کارمندان فقط اجازه ویرایش رزومه خودشان را داشته باشند
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        return obj.related_user == request.user

    # ۳. کارمندان فقط اجازه حذف رزومه خودشان را داشته باشند
    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        return obj.related_user == request.user

    # محافظت از فیلدهای حساس: غیرفعال کردن فیلدهای سئو و صاحب رزومه برای کارمندان عادی
    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            # این فیلدها برای کارمندان فقط‌خواندنی (Read-only) می‌شوند
            protected_fields = ['related_user','seo_priority', 'changefreq']
            for field in protected_fields:
                if field not in readonly:
                    readonly.append(field)
        return readonly

    # مقداردهی خودکار: اتصال اتوماتیک رزومه جدید به خودِ کارمندِ لاگین‌شده
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.related_user = request.user
        super().save_model(request, obj, form, change)

super_admin_site.register(Resume,ResumeAdmin)