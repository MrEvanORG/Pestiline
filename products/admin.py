from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import User, Product, ProductComponent, SiteSettings, ProductImage , MessageSiteSettings
from .models import Order, OrderItem

# --- تنظیمات پنل مدیریت اختصاصی ---
class PestilineAdminSite(admin.AdminSite):
    site_header = 'پنل ادمین پستیلاین'
    site_title = 'پنل ادمین'
    index_title = 'به پنل ادمین پستیلاین خوش آمدید'

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        for app in app_list:
            if app['app_label'] == 'products':
                app['name'] = 'مدیریت محصولات'
                custom_order = ['User', 'Product', 'Order', 'MessageSiteSettings','SiteSettings']
                app['models'].sort(key=lambda x: custom_order.index(x['object_name']) if x['object_name'] in custom_order else len(custom_order))
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
# در فایل admin.py ، بخش مربوط به ProductAdmin را با این کد جایگزین کنید:

# در فایل admin.py بخش ادمین Product را با این کد جایگزین کنید:

@admin.register(Product, site=super_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'seller_status', 'sale_method', 'price', 
        'stock', 'is_mixed', 'active_status'
    )
    
    list_filter = ('active_status', 'sale_method', 'is_mixed', 'is_free_shipping')
    search_fields = ('name', 'seller__username', 'seller__phone_number', 'seller__first_name', 'seller__last_name')
    inlines = [ProductComponentInline, ProductImageInline]
    prepopulated_fields = {'slug': ('name',)}
    
    # ۲. فیلدهای آمار فروش به بخش فقط خواندنی اضافه شدند تا در fieldsets قابل نمایش باشند
    readonly_fields = ('visit_count', 'get_sales_count', 'get_total_volume')

    # ۳. گروه‌بندی فیلدها (اضافه شدن آمار فروش به دسته‌بندی آمار سیستم)
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('name', 'slug', 'seller', 'active_status', 'description')
        }),
        ('تنظیمات مالی و نوع فروش', {
            'fields': ('sale_method', 'price', 'package_weight', 'is_mixed')
        }),
        ('موجودی و محدودیت‌های سفارش', {
            'fields': ('stock', 'min_order', 'max_order')
        }),
        ('اطلاعات ارسال', {
            'fields': ('is_free_shipping', 'time_tosend')
        }),
        ('آمار سیستم', {
            'fields': ('visit_count', 'get_sales_count', 'get_total_volume'),
            'classes': ('collapse',) # به صورت پیش‌فرض بسته است
        }),
    )

    # --------------------------------------------------------
    # متدهای اختصاصی نمایش
    # --------------------------------------------------------
    
    def seller_status(self, obj):
        return "پستیلاین" if obj.seller.is_superuser else obj.seller.username
    seller_status.short_description = "فروشنده"

    def get_sales_count(self, obj):
        return obj.sales_count
    get_sales_count.short_description = "تعداد فاکتور فروش"

    def get_total_volume(self, obj):
        unit = "کیلو" if obj.sale_method == 'BY_KILO' else "بسته"
        return f"{obj.total_volume_sold} {unit}"
    get_total_volume.short_description = "حجم کل فروش"

    # --------------------------------------------------------
    # اعتبارسنجی فرم‌ست‌ها
    # --------------------------------------------------------
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
        ('موقعیت جغرافیایی', {'fields': ('province', 'city','address','postal_code')}),
        ('سطوح دسترسی', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'), 'classes': ('collapse',)}),
        ('تاریخ‌های مهم', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    list_display = ('username', 'phone_number', 'province', 'city', 'is_staff')
    list_filter = ('is_superuser','is_staff')

@admin.register(MessageSiteSettings,site=super_admin_site)
class MessageSiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('primary_line_number',)}),
        ('ارسال پیامک به ادمین', {'fields': ('ta_new_user','ta_new_order','ta_cancell_order'),'classes': ('collapse',)}),
        ('ارسال پیامک به کاربر', {'fields': ('tu_wellcome','tu_submit_order','tu_send_order'),'classes': ('collapse',)}),
    )
    def has_delete_permission(self, request, obj=None): return False
    def has_add_permission(self, request): return not MessageSiteSettings.objects.exists()

@admin.register(SiteSettings, site=super_admin_site)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('وضعیت سایت', {'fields': ('status', 'maintenance_message','coming_soon_date','bypass_for_staff','bypass_for_superuser'),'classes': ('collapse',)}),
        ('سایر تنظیمات', {'fields': ('otp_time_interval',),'classes': ('collapse',)}),
        ('لینک های وبسایت', {'fields': ('link_phone1','link_phone2','link_prphone','link_mail','link_instagram','link_telegram','link_whatsapp','link_twitter','link_address','address_text'),'classes': ('collapse',)}),
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
    # اضافه شدن order_number به لیست نمایش
    list_display = ['order_number', 'customer', 'status', 'total_price_display', 'created_at']
    list_filter = ['status', 'created_at']
    # اضافه شدن order_number به فیلدهای جستجو
    search_fields = ['order_number', 'customer__phone_number', 'customer__last_name', 'tracking_code']
    inlines = [OrderItemInline]
    # order_number باید فقط خواندنی باشد
    readonly_fields = ['order_number', 'total_price', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات کلی', {
            'fields': ('order_number', 'customer', 'status', 'tracking_code')
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
        super().save_model(request, obj, form, change)
        obj.calculate_total()