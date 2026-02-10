from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import User, Product, ProductComponent , SiteSettings

# --- تنظیمات پنل مدیریت اختصاصی پستیلاین ---
class PestilineAdminSite(admin.AdminSite):
    site_header = 'پنل ادمین پستیلاین'
    site_title = 'پنل ادمین'
    index_title = 'به پنل ادمین پستیلاین خوش آمدید'

    def get_app_list(self, request,app_label=None):
        app_list = super().get_app_list(request,app_label)
        for app in app_list:
            if app['app_label'] == 'products':
                custom_order = ['Product', 'User'] # ترتیب نمایش مدل‌ها
                app['models'].sort(
                    key=lambda x: custom_order.index(x['object_name'])
                    if x['object_name'] in custom_order else len(custom_order)
                )
            if app['app_label'] == 'resume':
                custom_order = ['Resume'] # ترتیب نمایش مدل‌ها
                app['models'].sort(
                    key=lambda x: custom_order.index(x['object_name'])
                    if x['object_name'] in custom_order else len(custom_order)
                )

        return app_list

# ایجاد یک نمونه از پنل اختصاصی
super_admin_site = PestilineAdminSite(name='pestiline_admin')

# --- تنظیمات نمایش اینلاین اجزاء ---
class ProductComponentInline(admin.TabularInline):
    model = ProductComponent
    extra = 1 
    verbose_name = "نوع خاص پسته"
    verbose_name_plural = "نوع خاص پسته"

# --- مدیریت مدل محصول ---
@admin.register(Product, site=super_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller_status', 'sale_method', 'price', 'is_mixed')
    list_filter = ('sale_method', 'is_mixed')
    inlines = [ProductComponentInline]

    def seller_status(self, obj):
        return "پستیلاین" if obj.seller.is_superuser else obj.seller.username
    seller_status.short_description = "فروشنده"

    def save_formset(self, request, form, formset, change):
        """اعتبارسنجی مجموع درصدها در هنگام ذخیره محصول"""
        if formset.model == ProductComponent:
            total_percentage = 0
            count = 0
            
            # بررسی داده‌های فرم‌های اینلاین
            for f in formset.cleaned_data:
                if f and not f.get('DELETE', False):
                    total_percentage += f.get('percentage', 0)
                    count += 1

            product = form.instance
            if product.is_mixed:
                if count < 2:
                    raise ValidationError("محصول ترکیبی باید حداقل ۲ نوع پسته داشته باشد.")
                if total_percentage != 100:
                    raise ValidationError(f"مجموع درصدها باید ۱۰۰ باشد. مجموع فعلی: {total_percentage}")
            else:
                if count != 1:
                    raise ValidationError("محصول یکدست باید دقیقاً ۱ نوع پسته داشته باشد.")
                if total_percentage != 100:
                    raise ValidationError("درصد محصول یکدست باید ۱۰۰ باشد.")

        formset.save()

# --- مدیریت مدل کاربر ---
@admin.register(User, site=super_admin_site)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'is_superuser')

@admin.register(SiteSettings, site=super_admin_site)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('وضعیت سایت', {'fields': ('status', 'maintenance_message','coming_soon_date'),'classes': ('collapse',)}),
        ('لینک های وبسایت', {'fields': ('link_sitenumber','link_phone1','link_phone2','link_prphone','link_mail','link_instagram','link_telegram','link_whatsapp','link_twitter','link_address','address_text'),'classes': ('collapse',)}),
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()