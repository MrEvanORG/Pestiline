from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import User, Product, ProductComponent, SiteSettings, ProductImage , MessageSiteSettings
from .models import Order, OrderItem , Ticket , TicketMessage , NotificationLog
from products.templatetags.custom_filters import to_jalali
from django.db.models import Q
from django.urls import reverse

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
                custom_order = ['User', 'Product', 'Order', 'Ticket','NotificationLog','MessageSiteSettings','SiteSettings']
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
    readonly_fields = ('visit_count','get_sales_count', 'get_total_volume')

    # ۳. گروه‌بندی فیلدها (اضافه شدن آمار فروش به دسته‌بندی آمار سیستم)
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('slug', 'active_status','seo_priority','changefreq','visit_count')
        }),
        ('اطلاعات محصول', {
            'fields': ('name', 'seller', 'description')
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
        ('آمار ', {
            'fields': ( 'get_sales_count', 'get_total_volume'),
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
        js = ('products/js/admin_chained_cities.js',)
    
    fieldsets = (
        ('اطلاعات ورود', {'fields': ('username', 'password','prefered_notification'), 'classes': ('wide',)}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email', 'phone_number'), 'classes': ('extrapretty',)}),
        ('موقعیت جغرافیایی', {'fields': ('province', 'city','address','postal_code')}),
        ('سطوح دسترسی', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'), 'classes': ('collapse',)}),
        ('تاریخ‌های مهم', {'fields': ('tj_last_login', 'tj_date_joined'), 'classes': ('collapse',)}),
    )
    list_display = ('username', 'phone_number', 'province', 'city', 'is_staff')
    list_filter = ('is_superuser','is_staff')
    readonly_fields = ("tj_last_login","tj_date_joined")

    def tj_last_login(self, obj):
        return to_jalali(obj.last_login,form="persian_date_time")
    tj_last_login.short_description = "آخرین ورود"

    def tj_date_joined(self, obj):
        return to_jalali(obj.date_joined,form="persian_date_time")
    tj_date_joined.short_description = "تاریخ عضویت"

@admin.register(MessageSiteSettings,site=super_admin_site)
class MessageSiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('primary_line_number',)}),
        ('ارسال پیامک به ادمین', {'fields': ('ta_new_user','ta_new_order','ta_cancell_order','ta_new_ticket','ta_new_ticketmessage'),'classes': ('collapse',)}),
        ('ارسال پیامک به کاربر', {'fields': ('tu_wellcome','tu_submit_order','tu_send_order','tu_new_ticketmessage'),'classes': ('collapse',)}),
    )
    def has_delete_permission(self, request, obj=None): return False
    def has_add_permission(self, request): return not MessageSiteSettings.objects.exists()

@admin.register(SiteSettings, site=super_admin_site)
class SiteSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ('total_views','today_views','this_week_views','this_month_views','this_year_views','tj_last_reset_date','test_maintenance','test_commingsoon','test_developing')
    fieldsets = (
        ('وضعیت سایت', {'fields': ('status', 'maintenance_message','coming_soon_date','bypass_for_staff','bypass_for_superuser','welcome_song'),'classes': ('collapse',)}),
        ('لینک های تست', {'fields': ('test_commingsoon', 'test_maintenance','test_developing'),'classes': ('collapse',)}),
        ('سایر تنظیمات', {'fields': ('otp_time_interval',),'classes': ('collapse',)}),
        ('لینک های وبسایت', {'fields': ('link_phone1','link_phone2','link_prphone','link_mail','link_instagram','link_telegram','link_whatsapp','link_twitter','link_address','address_text'),'classes': ('collapse',)}),
        ('بازدید های وبسایت', {'fields': ('total_views','today_views','this_week_views','this_month_views','this_year_views','tj_last_reset_date'),'classes': ('collapse',)}),
    )
    def tj_last_reset_date(self,obj):
        return to_jalali(obj.last_reset_date,form="persian_date")
    tj_last_reset_date.short_description = "زمان آخرین ریست تاریخ"

    def test_commingsoon(self,obj):
        url = '#'
        try:
            url = reverse('comming_soon')
        except:pass
        return format_html('<a class="button" target="_blank" style="font-family:Vazirmatn;text-decoration:none;" href="{}">مشاهده</a>',url)
    test_commingsoon.short_description = "تست صفحه کامینگ سون"

    def test_maintenance(self,obj):
        url = '#'
        try:
            url = reverse('maintenance')
        except:pass
        return format_html('<a class="button" target="_blank" style="font-family:Vazirmatn;text-decoration:none;" href="{}">مشاهده</a>',url)
    test_maintenance.short_description = "تست صفحه در حال آپدیت"

    def test_developing(self,obj):
        url = '#'
        try:
            url = reverse('developing')
        except:pass
        return format_html('<a class="button" target="_blank" style="font-family:Vazirmatn;text-decoration:none;" href="{}">مشاهده</a>',url)
    test_developing.short_description = "تست صفحه درحال توسعه"

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
    readonly_fields = ['order_number', 'total_price', 'tj_created_at', 'tj_updated_at']
    
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
            'fields': ('tj_created_at', 'tj_updated_at')
        }),
    )

    def tj_created_at(self,obj):
        return to_jalali(obj.created_at,form="persian_date_time")
    tj_created_at.short_description = "تاریخ ایجاد"

    def tj_updated_at(self,obj):
        return to_jalali(obj.updated_at,form="persian_date_time")
    tj_updated_at.short_description = "آخرین آپدیت"

    def total_price_display(self, obj):
        return f"{int(obj.total_price):,} تومان"
    total_price_display.short_description = "مبلغ کل"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_total()

from django.contrib import admin
from .models import Ticket, TicketMessage, User
from products.templatetags.custom_filters import to_jalali

# --- اینلاین پیام‌های گفتگو ---
class TicketMessageInline(admin.StackedInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ['tj_created_at']
    fields = ['sender', 'reply_to', 'text', 'attachment',  'tj_created_at']

    def tj_created_at(self, obj):
        if obj.pk:
            return to_jalali(obj.created_at, form="persian_date_time")
        return "-"
    tj_created_at.short_description = "زمان ارسال"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.resolver_match and request.resolver_match.kwargs.get('object_id'):
            ticket_id = request.resolver_match.kwargs.get('object_id')
            ticket = Ticket.objects.get(pk=ticket_id)
            
            # ۱. محدود کردن لیست پیام‌ها برای فیلد ریپلای
            if db_field.name == "reply_to":
                kwargs["queryset"] = TicketMessage.objects.filter(ticket_id=ticket_id).order_by('created_at')

            # ۲. محدود کردن لیست کشویی فرستنده (Sender)
            if db_field.name == "sender":
                allowed_users_ids = [ticket.user.id]
                if ticket.responder:
                    allowed_users_ids.append(ticket.responder.id)
                else:
                    # اگر مسئولی نداره، ادمین فعلی رو تو لیست بذار تا بتونه پیام بده
                    allowed_users_ids.append(request.user.id)
                kwargs["queryset"] = User.objects.filter(id__in=allowed_users_ids)
                
        else:
            if db_field.name == "reply_to":
                kwargs["queryset"] = TicketMessage.objects.none()
                
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class AdminUsersFilter(admin.SimpleListFilter):
    # عنوانی که در پنل سمت راست (بخش فیلترها) نمایش داده می‌شود
    title = 'ادمین / کارمند مرتبط'
    
    # نام پارامتری که در URL قرار می‌گیرد (مثلا ?staff_user=2)
    parameter_name = 'staff_user'

    def lookups(self, request, model_admin):
        """
        این متد گزینه‌هایی که در لیست فیلتر نمایش داده می‌شوند را مشخص می‌کند.
        خروجی باید یک لیست از تاپل‌ها (Tuples) باشد: (value, display_name)
        """
        # فقط کاربرانی که کارمند یا سوپریوزر هستند را واکشی می‌کنیم
        staff_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
        
        # ساخت لیست تاپل‌ها برای نمایش در پنل
        # اگر کاربر نام کامل داشت آن را نشان بده، وگرنه یوزرنیم
        return [
            (user.id, user.get_full_name() or user.username) 
            for user in staff_users
        ]

    def queryset(self, request, queryset):
        """
        این متد دیتابیس را بر اساس گزینه انتخاب شده فیلتر می‌کند.
        """
        # اگر گزینه‌ای انتخاب شده بود (مقدار آن در self.value() قرار می‌گیرد)
        if self.value():
            # دقت کنید که نام فیلد در مدل شما چیست. 
            # اگر فیلد مدل شما user است، مینویسیم user_id. 
            # اگر responder است، مینویسیم responder_id
            return queryset.filter(user_id=self.value())
            
        # اگر چیزی انتخاب نشده بود، همه را برگردان
        return queryset
# --- ادمین گفتگو و پشتیبانی ---
@admin.register(Ticket, site=super_admin_site) # با فرض اینکه super_admin_site را ایمپورت کرده‌اید
class TicketAdmin(admin.ModelAdmin):
    # استفاده از متد کاستوم برای نمایش هشتگ
    list_display = ('formatted_ticket_number', 'user', 'subject_type', 'status', 'responder', 'tj_updated_at')
    list_filter = ('status',AdminUsersFilter, 'subject_type', 'created_at')
    search_fields = ('ticket_number', 'user__username', 'user__phone_number', 'responder__username')
    inlines = [TicketMessageInline]
    
    readonly_fields = ('formatted_ticket_number', 'responder', 'tj_created_at', 'tj_updated_at')

    fieldsets = (
        ('اطلاعات گفتگو', {
            # بجای ticket_number فیلد کاستوم رو میذاریم
            'fields': ('formatted_ticket_number', 'user', 'responder', 'subject_type', 'status')
        }),
        ('لینک‌های مرتبط', {
            'fields': ('order', 'product'),
            'classes': ('collapse',),
            'description': 'این فیلدها با توجه به موضوع گفتگو پر می‌شوند.'
        }),
        ('زمان‌بندی', {
            'fields': ('tj_created_at', 'tj_updated_at')
        }),
    )

    # نمایش هشتگ در پنل
    def formatted_ticket_number(self, obj):
        if obj.ticket_number:
            return f"#{obj.ticket_number}"
        return "-"
    formatted_ticket_number.short_description = "شماره پیگیری"
    formatted_ticket_number.admin_order_field = 'ticket_number' # برای حفظ قابلیت مرتب‌سازی

    def tj_created_at(self, obj):
        return to_jalali(obj.created_at, form="persian_date_time")
    tj_created_at.short_description = "تاریخ ایجاد"

    def tj_updated_at(self, obj):
        return to_jalali(obj.updated_at, form="persian_date_time")
    tj_updated_at.short_description = "آخرین آپدیت"

    # --- جادوی ثبت خودکار فرستنده ---
    def save_formset(self, request, form, formset, change):
        if formset.model == TicketMessage:
            instances = formset.save(commit=False)
            for instance in instances:
                # اگر فیلد فرستنده خالی گذاشته شده بود، کاربری که لاگین هست رو به عنوان فرستنده بذار
                if not instance.sender:
                    instance.sender = request.user
                instance.save()
            formset.save_m2m()
        else:
            super().save_formset(request, form, formset, change)


@admin.register(NotificationLog,site=super_admin_site)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'status', 'tj_created_at')
    list_filter = ('notification_type','related_event', 'status', 'created_at')
    search_fields = ('user__username', 'user__phone_number', 'message_content', 'error_details')
    
    # نمایش فیلدها در صفحه جزئیات
    fieldsets = (
        ('اطلاعات گیرنده', {
            'fields': ('user', 'notification_type','related_event')
        }),
        ('محتوای پیام', {
            'fields': ('message_content',)
        }),
        ('وضعیت ارسال', {
            'fields': ('status', 'error_details', 'tj_created_at')
        }),
    )

    readonly_fields = ('tj_created_at',)
    # readonly_fields = ('user', 'notification_type' 'message_content', 'status', 'error_details', 'tj_created_at')

    # غیرفعال کردن قابلیت افزودن گزارش دستی از پنل ادمین
    def has_add_permission(self, request):
        return True

    # غیرفعال کردن قابلیت ویرایش گزارش‌های ثبت شده
    def has_change_permission(self, request, obj=None):
        return False
        
    # در صورت نیاز می‌توانید حذف را هم غیرفعال کنید:
    # def has_delete_permission(self, request, obj=None):
    #     return False

    def tj_created_at(self, obj):
        return to_jalali(obj.created_at, form="persian_date_time")
    tj_created_at.short_description = "زمان ارسال"
