from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import User, Product, ProductComponent, SiteSettings, ProductImage
from .models import Order, OrderItem

# --- تنظیمات پنل مدیریت اختصاصی ---
class PestilineAdminSite(admin.AdminSite):
    site_header = 'پنل ادمین پستیلاین'
    site_title = 'پنل ادمین'
    index_title = 'به پنل ادمین پستیلاین خوش آمدید'

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        # (کد مرتب‌سازی شما اینجا حفظ شود)
        return app_list

super_admin_site = PestilineAdminSite(name='pestiline_admin')

# --- اینلاین‌ها ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            # اینجا چون settings.MEDIA_URL را تنظیم کردیم، obj.image.url درست کار می‌کند
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "بدون تصویر"
    image_preview.short_description = "پیش‌نمایش"

class ProductComponentInline(admin.TabularInline):
    model = ProductComponent
    extra = 1 
    verbose_name = "نوع خاص پسته"
    verbose_name_plural = "نوع خاص پسته"

# --- ادمین‌ها ---
@admin.register(Product, site=super_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller_status', 'sale_method', 'price', 'is_mixed')
    list_filter = ('sale_method', 'is_mixed')
    search_fields = ('name',)
    inlines = [ProductComponentInline, ProductImageInline]

    def seller_status(self, obj):
        return "پستیلاین" if obj.seller.is_superuser else obj.seller.username
    seller_status.short_description = "فروشنده"

    def save_formset(self, request, form, formset, change):
        if formset.model == ProductComponent:
            total_percentage = 0
            count = 0
            for f in formset.cleaned_data:
                if f and not f.get('DELETE', False):
                    total_percentage += f.get('percentage', 0)
                    count += 1

            product = form.instance
            if product.is_mixed:
                if count < 2:
                    raise ValidationError("محصول ترکیبی باید حداقل ۲ نوع پسته داشته باشد.")
                if total_percentage != 100:
                    raise ValidationError(f"مجموع درصدها باید ۱۰۰ باشد. فعلی: {total_percentage}")
            else:
                if count != 1:
                    raise ValidationError("محصول یکدست باید دقیقاً ۱ نوع پسته داشته باشد.")
                if total_percentage != 100:
                    raise ValidationError("درصد محصول یکدست باید ۱۰۰ باشد.")
        
        formset.save()

@admin.register(User, site=super_admin_site)
class CustomUserAdmin(UserAdmin):
    class Media:
        js = ('js/admin_chained_cities.js',)
    
    fieldsets = (
        ('اطلاعات ورود', {'fields': ('username', 'password'), 'classes': ('wide',)}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email', 'phone_number'), 'classes': ('extrapretty',)}),
        ('موقعیت جغرافیایی', {'fields': ('province', 'city')}),
        ('سطوح دسترسی', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'), 'classes': ('collapse',)}),
        ('تاریخ‌های مهم', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    list_display = ('username', 'phone_number', 'province', 'city', 'is_staff')
    list_filter = ('province', 'is_staff')

@admin.register(SiteSettings, site=super_admin_site)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('وضعیت سایت', {'fields': ('status', 'maintenance_message','coming_soon_date','otp_time_interval'),'classes': ('collapse',)}),
        ('لینک های وبسایت', {'fields': ('link_sitenumber','link_phone1','link_phone2','link_prphone','link_mail','link_instagram','link_telegram','link_whatsapp','link_twitter','link_address','address_text'),'classes': ('collapse',)}),
    )
    def has_delete_permission(self, request, obj=None): return False
    def has_add_permission(self, request): return not SiteSettings.objects.exists()


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['get_cost_display']
    raw_id_fields = ['product'] # برای سرعت بیشتر در لود محصولات
    
    def get_cost_display(self, obj):
        return f"{int(obj.get_cost()):,} تومان"
    get_cost_display.short_description = "قیمت کل"

@admin.register(Order,site=super_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'total_price_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'customer__phone_number', 'customer__last_name', 'tracking_code']
    inlines = [OrderItemInline]
    readonly_fields = ['total_price', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات کلی', {
            'fields': ('customer', 'status', 'tracking_code')
        }),
        ('اطلاعات ارسال', {
            'fields': ('receiver_name', 'receiver_phone', 'address', 'postal_code')
        }),
        ('اطلاعات مالی', {
            'fields': ('shipping_cost', 'total_price')
        }),
        ('زمان‌بندی', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def total_price_display(self, obj):
        return f"{int(obj.total_price):,} تومان"
    total_price_display.short_description = "مبلغ کل"

    def save_model(self, request, obj, form, change):
        # ذخیره سفارش
        super().save_model(request, obj, form, change)
        # محاسبه مجدد قیمت (اگر هزینه ارسال دستی تغییر کرده باشد)
        obj.calculate_total()