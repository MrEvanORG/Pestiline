import os
import sys
import uuid
import random
from io import BytesIO
from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.db.models import Sum
from PIL import Image as PilImage
from django.utils import timezone
from seo.models import ChangeFreqChoices
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator , FileExtensionValidator
# --- گرفتن محل ذخیره عکس محصول ---
def get_file_path(instance, filename):
    """
    ذخیره فایل در پوشه: media/products_photos/{product_id}/unique_name.jpg
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    # تغییر مسیر به پوشه درخواستی شما
    return os.path.join(f'products_photos/{instance.product.id}/', filename)

# --- تابع فشرده سازی عکس محصول ---
def compress_image(image, max_size_kb=500, max_width=1200):
    im = PilImage.open(image)
    output = BytesIO()
    
    if im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    
    # تغییر سایز هوشمند بر اساس ورودی
    if im.width > max_width:
        ratio = max_width / im.width
        new_height = int(im.height * ratio)
        im = im.resize((max_width, new_height), PilImage.Resampling.LANCZOS)

    # شروع با کیفیت عالی و روشن کردن بهینه‌ساز پیش‌فرض
    quality = 95
    step = 4  # کاهش ملایم‌تر کیفیت
    
    im.save(output, format='JPEG', quality=quality, optimize=True)
    
    # حلقه فشرده‌سازی تا رسیدن به زیر حجم مدنظر یا حداقل کیفیت مجاز
    while output.tell() > max_size_kb * 1024 and quality > 30:
        output.seek(0)
        output.truncate(0)
        quality -= step
        im.save(output, format='JPEG', quality=quality, optimize=True)

    output.seek(0)
    
    return InMemoryUploadedFile(
        output, 
        'ImageField', 
        f"{image.name.split('.')[0]}.jpg", 
        'image/jpeg', 
        sys.getsizeof(output), 
        None
    )

# --- توابع کمکی فایل‌های پشتیبانی ---
def ticket_file_upload_path(instance, filename):
    return f'support_tickets/{instance.ticket.ticket_number}/{filename}'

# --- توابع کمکی سایز فایل ضمائم پشتیبانی ---
def validate_file_size(value):
    limit = 5 * 1024 * 1024  # 5 مگابایت
    if value.size > limit:
        raise ValidationError('حجم فایل نباید بیشتر از 5 مگابایت باشد.')
    
def validate_file_size_music(value):
    limit = 12 * 1024 * 1024  # 
    if value.size > limit:
        raise ValidationError('حجم فایل نباید بیشتر از 12 مگابایت باشد.')

# --- تنظیمات سایت ---
class SiteSettings(models.Model):
    SITE_STATUS_CHOICES = [
        ('ACTIVE', 'فعال'),
        ('MAINTENANCE', 'در حال بروزرسانی (Maintenance)'),
        ('COMING_SOON', 'بزودی (Coming Soon)'),
    ]

    status = models.CharField(max_length=15, choices=SITE_STATUS_CHOICES, default='ACTIVE', verbose_name="وضعیت سایت")
    maintenance_message = models.TextField(blank=True, null=True, verbose_name="متن صفحه بروزرسانی")
    coming_soon_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ و زمان بازگشایی")
    welcome_song = models.FileField(
        upload_to='settings/audio/', 
        null=True, 
        blank=True, 
        verbose_name="آهنگ صفحه Coming Soon",
        validators=[FileExtensionValidator(allowed_extensions=['mp3']), validate_file_size],
        help_text="فرمت MP3، حداکثر حجم 12 مگابایت. اگر خالی باشد، آهنگی پخش نخواهد شد."
    )
    otp_time_interval = models.PositiveIntegerField(default=120, verbose_name="زمان انتظار ارسال مجدد کد (ثانیه)")
    bypass_for_staff = models.BooleanField(
        default=False, 
        verbose_name="دسترسی آزاد برای کارمندان", 
        help_text="اگر فعال باشد، کاربرانی که تیک 'کارمند' دارند، سایت را به صورت عادی مشاهده خواهند کرد."
    )
    bypass_for_superuser = models.BooleanField(
        default=False, 
        verbose_name="دسترسی آزاد برای ابرکاربر", 
        help_text="اگر فعال باشد، کاربرانی که تیک 'ابرکاربر' دارند، سایت را به صورت عادی مشاهده خواهند کرد."
    )

    link_phone1 = models.CharField(max_length=100,verbose_name='لینک تماس 1',null=True,blank=True)
    link_phone2 = models.CharField(max_length=100,verbose_name='لینک تماس 2',null=True,blank=True)
    link_prphone = models.CharField(max_length=100,verbose_name='لینک تلفن ثابت',null=True,blank=True)
    link_sitenumber = models.CharField(max_length=100,verbose_name='لینک شماره ارسال پیامک ثابت',null=True,blank=True)
    link_mail = models.CharField(max_length=100,verbose_name='لینک ایمیل سایت',null=True,blank=True)
    link_instagram = models.CharField(max_length=100,verbose_name='لینک اینستاگرام',null=True,blank=True)
    link_whatsapp = models.CharField(max_length=100,verbose_name='لینک واتساپ',null=True,blank=True)
    link_telegram = models.CharField(max_length=100,verbose_name='لینک تلگرام',null=True,blank=True)
    link_twitter = models.CharField(max_length=100,verbose_name='لینک توییتر',null=True,blank=True)
    link_address = models.CharField(max_length=100,verbose_name='لینک آدرس',null=True,blank=True)
    address_text = models.CharField(max_length=100,verbose_name='متن آدرس',null=True,blank=True)

    total_views = models.PositiveIntegerField(default=0,verbose_name='تعداد کل بازدید ها')
    today_views = models.PositiveIntegerField(default=0,verbose_name='بازدید های امروز')
    this_week_views = models.PositiveIntegerField(default=0,verbose_name='بازدیدهای این هفته')
    this_month_views = models.PositiveIntegerField(default=0,verbose_name='بازدید های این ماه')
    this_year_views = models.PositiveIntegerField(default=0,verbose_name='بازدید های امسال')
    last_reset_date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("فقط یک تنظیمات کلی برای سایت می‌تواند وجود داشته باشد.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return "تنظیمات عمومی پستیلاین"

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

# --- تنظیمات پیامکی سایت ---
class MessageSiteSettings(models.Model):
    class NotifStatusChoices(models.TextChoices):
        DISABLE = "DISABLE","غیر فعال"
        ENABLE = "ENABLE","فعال"

    # ta : to admin
    # tu : to user
    # ts : to staff

    # ---------- To Admin Message Section ----------

    ta_new_user = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='کاربر جدید',
        help_text='اطلاع رسانی به ادمین سیگنال کاربر جدید',
    )
    
    ta_new_order = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='سفارش جدید',
        help_text='اطلاع رسانی به ادمین سیگنال سفارش جدید',
    )

    ta_cancell_order = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='لغو سفارش',
        help_text='اطلاع رسانی به ادمین سیگنال لغو سفارش\nلغو سفارش توسط کاربر پس از تایید سبد خرید و قبل از پرداخت  هزینه .'
    )
    ta_new_ticket = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='تیکت جدید',
        help_text='اطلاع رسانی به ادمین ایجاد تیکت جدید توسط کاربر .'
    )
    ta_new_ticketmessage = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='پیام جدید روی تیکت',
        help_text='اطلاع رسانی به ادمین ایجاد پیام روی تیکت قبلی .'   
    )
    #---------- To User Message Section ----------
    tu_wellcome = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='خوشامدگویی',
        help_text='خوشامدگویی به کاربر پس از ثبت نام',
        )
    tu_submit_order = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='ثبت سفارش',
        help_text='اطلاع رسانی به کاربر پس از ثبت شدن سفارش و ارسال کد پیگیری سفارش'
    )
    tu_send_order = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='ارسال سفارش',
        help_text='اطلاع رسانی به کاربر پس از ارسال سفارش و ارسال کد پیگیری پستی'
    )
    tu_new_ticketmessage = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='پیام جدید روی تیکت',
        help_text='اطلاع رسانی به کاربر ایجاد پیام روی تیکت ایجاد شده قبلی .'   
    )

    tu_new_ticket = models.CharField(
        max_length=8,
        choices=NotifStatusChoices,
        default=NotifStatusChoices.DISABLE,
        verbose_name='ثبت تیکت',
        help_text='اطلاع رسانی به کاربر پس از ثبت موفق تیکت پشتیبانی.'
    )
    
    primary_line_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='شماره ارسال پیامک',
    )

    def __str__(self):
        return "تنظیمات اطلاع رسانی پستیلاین"

    class Meta:
        verbose_name = "تنظیمات اطلاع رسانی"
        verbose_name_plural = "تنظیمات اطلاع رسانی"

# --- مدل‌های پایه (استان و شهر) ---
class Province(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام استان")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "استان"
        verbose_name_plural = "استان‌ها"

class City(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities', verbose_name="استان")
    name = models.CharField(max_length=100, verbose_name="نام شهر")

    def __str__(self):
        return f"{self.name} ({self.province.name})"
    
    class Meta:
        verbose_name = "شهر" 
        verbose_name_plural = "شهرها"

# --- مدل کاربر ---
class User(AbstractUser):

    class PrederefNotifChoices(models.TextChoices):
        MESSAGE = "MESSAGE","پیامک"
        EMAIL = "EMAIL","ایمیل"
        DISABLE = "DISABLE","غیرفعال"

    phone_regex = RegexValidator(regex=r'^09\d{9}$', message="شماره موبایل باید ۱۱ رقم بوده و با ۰۹ شروع شود.")
    phone_number = models.CharField(validators=[phone_regex], max_length=11, unique=True, verbose_name="شماره همراه")
    address = models.TextField(null=True, blank=True, verbose_name="آدرس پستی")
    postal_code = models.CharField(max_length=10, null=True, blank=True, verbose_name="کد پستی")
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="استان")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="شهر")
    prefered_notification = models.CharField(max_length=8,choices=PrederefNotifChoices,default=PrederefNotifChoices.MESSAGE,verbose_name='ترجیح اطلاع رسانی',help_text='* درخواست های همکاری رزومه در هر حالتی و همیشه به صورت ایمیل ارسال میشوند')
    #اطلاع رسانی های پستیلاین شامل اعلان های ثبت سفارش / پاسخ داده شدن تیک ها / ارسال کد های پیگیری پستی یا کد های پیگیری سفارش هستند

    def clean(self):
        super().clean()
        if self.province and self.city and self.city.province != self.province:
            raise ValidationError({'city': f"شهر '{self.city.name}' متعلق به استان '{self.province.name}' نیست."})

    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"
    
    class Meta:
        verbose_name = "کاربر" 
        verbose_name_plural = "کاربران"

from django.contrib.auth import get_user_model
User = get_user_model() # type: ignore

# --- مدل محصول ---
class Product(models.Model):
    PISTACHIO_TYPES = [('AKBARI', 'اکبری'), ('FANDOGHI', 'فندقی'), ('AHMAD_AGHAEI', 'احمدآقایی'), ('KALEH_GHOOCHI', 'کله قوچی')]
    SALE_METHODS = [('PACKAGED', 'بسته‌ای'), ('BY_KILO', 'کیلویی')]

    slug = models.SlugField(max_length=220, unique=True, allow_unicode=True, verbose_name="آدرس یکتا (Slug)", null=True)
    active_status = models.BooleanField(default=True, verbose_name='وضعیت نمایش محصول و انتشار سایت مپ',help_text='برای سئو بهتر بجای غیرفعال کردن محصول را ناموجود کنید.')
    seo_priority = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        default=0.8,  # <--- مقدار جدید
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='اولویت سئو'
    )

    # تغییر دیفالت فرکانس تغییر برای محصول به WEEKLY
    changefreq = models.CharField(
        max_length=20, 
        choices=ChangeFreqChoices.choices, 
        default=ChangeFreqChoices.MONTHLY,  # <--- مقدار جدید
        verbose_name='فرکانس تغییر'
    )
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', verbose_name="فروشنده", help_text='فروشنده ابرکاربر پستیلاین تلقی میشود .')
    ounce = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(14), MaxValueValidator(60)],
        verbose_name="اونس (تعداد مغز در هر اونس)",
        help_text='عدد صحیح بین ۱۴ تا ۶۰. هرچه عدد کمتر باشد، پسته درشت‌تر است. اختیاری'
    )
    harvest_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1300), MaxValueValidator(1499)],
        verbose_name="سال برداشت",
        help_text='سال شمسی برداشت، عدد صحیح بین ۱۳۰۰ تا ۱۴۹۹ (مثلا: ۱۴۰۵). اختیاری'
    )
    name = models.CharField(max_length=220, verbose_name="نام محصول")
    sale_method = models.CharField(max_length=20, choices=SALE_METHODS, verbose_name="نوع فروش")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="قیمت (تومان)", help_text='برای هر کیلوگرم یا هر بسته')
    package_weight = models.FloatField(null=True, blank=True, verbose_name="وزن هر بسته (کیلو)", help_text='درصورت فروش بسته ای وارد کنید')
    stock = models.FloatField(verbose_name="موجودی", help_text='درصورت ناموجود بودن محصول عدد 0 وارد شود')
    min_order = models.FloatField(default=1, verbose_name="کف سفارش", help_text='تعداد بسته یا کیلوگرم')
    max_order = models.FloatField(default=100, verbose_name="سقف سفارش", help_text='تعداد بسته یا کیلوگرم')
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات کامل محصول",help_text='اختیاری')
    visit_count = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")
    is_mixed = models.BooleanField(default=False, verbose_name="آیا محصول ترکیبی است؟")
    is_free_shipping = models.BooleanField(default=False, verbose_name='دارای ارسال رایگان است ؟')
    time_tosend = models.CharField(null=True, max_length=50, verbose_name='متن مدت زمان ارسال', help_text='مثلا : تحویل به پست تا 3 روز کاری')
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    def clean(self):
        super().clean()
        if self.sale_method == 'PACKAGED' and not self.package_weight:
            raise ValidationError("برای فروش بسته‌ای، وارد کردن وزن هر بسته الزامی است.")

        # بازه مجاز اونس و سال برداشت
        range_errors = {}
        if self.ounce is not None and not (14 <= self.ounce <= 60):
            range_errors['ounce'] = ValidationError(
                'اونس باید عددی بین ۱۴ تا ۶۰ باشد.',
                code='ounce_out_of_range'
            )
        if self.harvest_year is not None and not (1300 <= self.harvest_year <= 1499):
            range_errors['harvest_year'] = ValidationError(
                'سال برداشت باید عددی بین ۱۳۰۰ تا ۱۴۹۹ باشد (مثلا: ۱۴۰۵).',
                code='year_out_of_range'
            )
        if range_errors:
            raise ValidationError(range_errors)

        if self.sale_method == 'PACKAGED':
            errors = {}
            if self.min_order and self.min_order % 1 != 0:
                errors['min_order'] = ValidationError(
                    'برای فروش بسته‌ای، کف سفارش باید یک عدد صحیح باشد (مثلا: ۴) و نمی‌تواند اعشاری باشد (مثلا: ۴.۲).',
                    code='not_an_integer'
                )
            if self.max_order and self.max_order % 1 != 0:
                errors['max_order'] = ValidationError(
                    'برای فروش بسته‌ای، سقف سفارش باید یک عدد صحیح باشد (مثلا: ۱۰۰).',
                    code='not_an_integer'
                )
            if errors:
                raise ValidationError(errors)

    # متدهای کمکی
    def get_dynamic_title(self):
        comps = self.components.all() # type: ignore
        if not comps.exists(): return self.name
        type_map = dict(self.PISTACHIO_TYPES)
        shell_map = dict(ProductComponent.SHELL_CHOICES)
        types = [type_map.get(c.pistachio_type) for c in comps]
        shells = [shell_map.get(c.shell_status) for c in comps]
        unique_shells = set(shells)
        if len(unique_shells) == 1:
            joined_types = " و ".join(types) # type: ignore
            return f"پسته {joined_types} {shells[0]}"
        else:
            parts = [f"{type_map.get(c.pistachio_type)} {shell_map.get(c.shell_status)}" for c in comps]
            return "پسته " + " و ".join(parts)

    def get_dynamic_processing(self):
        comps = self.components.all() # type: ignore
        if not comps.exists(): return ""
        proc_map = dict(ProductComponent.PROCESSING_CHOICES)
        procs = [proc_map.get(c.processing) for c in comps]
        if len(set(procs)) == 1:
            return f"{procs[0]}"
        else:
            type_map = dict(self.PISTACHIO_TYPES)
            parts = [f"{type_map.get(c.pistachio_type)} {proc_map.get(c.processing)}" for c in comps]
            return " و ".join(parts)

    def get_quality_badge(self):
        comps = self.components.all() # type: ignore
        qualities = [c.quality for c in comps]
        if 'LUXARY' in qualities: return {'text': 'دستچین اعلاء', 'class': 'luxury'}
        elif 'STANDARD' in qualities: return {'text': 'استاندارد', 'class': 'standard'}
        elif 'ECONOMY' in qualities: return {'text': 'اقتصادی', 'class': 'economy'}
        return None
    
    def get_composition_list(self):
        if not self.is_mixed: return None
        return self.components.all().order_by('-percentage')
    
    @property
    def sales_count(self):
        """
        تعداد دفعاتی که این محصول در سفارشات معتبر ثبت شده است.
        """
        valid_statuses = ['PROCESSING', 'SHIPPED', 'DELIVERED']
        # از orderitem_set برای دسترسی معکوس از محصول به اقلام سفارش استفاده می‌کنیم
        return self.orderitem_set.filter(order__status__in=valid_statuses).count()

    @property
    def total_volume_sold(self):
        """
        مجموع مقدار فروخته شده (مجموع کیلوگرم یا تعداد بسته‌ها)
        """
        valid_statuses = [ 'PROCESSING', 'SHIPPED', 'DELIVERED']
        result = self.orderitem_set.filter(
            order__status__in=valid_statuses
        ).aggregate(total=Sum('quantity'))
        
        return result['total'] or 0
    
    def get_absolute_url(self):
        return reverse("product_detail", args=[self.slug])
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "محصول" 
        verbose_name_plural = "محصولات"

# --- مدل اجزای تشکیل‌دهنده ---
class ProductComponent(models.Model):
    PROCESSING_CHOICES = [('RAW', 'خام'), ('ROASTED', 'شور/بو داده')]
    SHELL_CHOICES = [('OPEN', 'خندان'), ('CLOSED', 'دهن‌ بست')]
    QUALITY_CHOICES = [('LUXARY','دستچین / اعلاء'),('STANDARD','استاندارد / معمولی') ,('ECONOMY','اقتصادی')]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='components')
    pistachio_type = models.CharField(max_length=20, choices=Product.PISTACHIO_TYPES, verbose_name="نوع پسته")
    processing = models.CharField(max_length=10, choices=PROCESSING_CHOICES, verbose_name="فرآوری")
    shell_status = models.CharField(max_length=10, choices=SHELL_CHOICES, verbose_name="وضعیت دهان")
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, verbose_name='کیفیت', null=True)
    percentage = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], verbose_name="درصد تشکیل‌دهنده")

    def __str__(self): return f"نوع خاص {self.pk}"
    class Meta: verbose_name = "نوع خاص پسته"; verbose_name_plural = "نوع خاص پسته"

# --- مدل تصاویر محصول ---
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="محصول")
    image = models.ImageField(upload_to=get_file_path, verbose_name="تصویر")
    alt_text = models.CharField(max_length=100, blank=True, null=True, verbose_name="متن جایگزین (SEO)")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image:
            if not self.pk: # عکس جدید
                self.image = compress_image(self.image)
            else: # آپدیت عکس
                try:
                    old = ProductImage.objects.get(pk=self.pk)
                    if self.image.name != old.image.name:
                        self.image = compress_image(self.image)
                except ProductImage.DoesNotExist:
                    pass
        super().save(*args, **kwargs)

    def __str__(self): return f"عکس {self.product.name}"
    class Meta: verbose_name = "تصویر محصول"; verbose_name_plural = "گالری تصاویر"

# --- مدل سفارشات ---
class Order(models.Model):
    STATUS_CHOICES = [
        ('CART', 'سبد خرید (در انتظار تکمیل)'),
        ('PENDING', 'در انتظار پرداخت (تایید شده)'),
        ('PROCESSING', 'در حال پردازش (تایید پرداخت)'),
        ('SHIPPED', 'ارسال شده'),
        ('DELIVERED', 'تحویل شده'),
        ('CANCELED', 'لغو شده'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="مشتری")
    
    # فیلد کد پیگیری اختصاصی و یکتای سایت (اضافه شده)
    order_number = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="شماره سفارش")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="وضعیت")
    
    # اطلاعات گیرنده (بدون شهر و استان طبق ساختار جدید)
    receiver_name = models.CharField(max_length=100, verbose_name="نام گیرنده")
    receiver_phone = models.CharField(max_length=15, verbose_name="شماره تماس گیرنده")
    address = models.TextField(verbose_name="آدرس دقیق پستی")
    postal_code = models.CharField(max_length=20, verbose_name="کد پستی")

    # اطلاعات مالی
    shipping_cost = models.DecimalField(
        max_digits=10, decimal_places=0, 
        null=True, blank=True, 
        verbose_name="هزینه ارسال"
    )
    total_price = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ قابل پرداخت")
    
    # سایر فیلدها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")
    
    # کدی که اداره پست برای پیگیری می‌دهد
    tracking_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="کد پیگیری پستی")

# در فایل models.py - متد save در کلاس Order

    def save(self, *args, **kwargs):
        # تولید خودکار شماره سفارش ۵ رقمی عددی
        if not self.order_number:
            while True:
                # تولید یک عدد تصادفی بین 10000 تا 99999
                random_code = random.randint(10000, 99999)
                new_number = f"PST-{random_code}"
                
                if not Order.objects.filter(order_number=new_number).exists():
                    self.order_number = new_number
                    break
                    
        super().save(*args, **kwargs)

    def calculate_total(self):
        """محاسبه مجدد قیمت کل سفارش"""
        items_total = sum(item.get_cost() for item in self.items.all())
        shipping = self.shipping_cost if self.shipping_cost else 0
        self.total_price = items_total + shipping
        self.save()

    def __str__(self):
        # نمایش شماره سفارش اختصاصی در پنل ادمین
        return f"سفارش {self.order_number} - {self.customer.get_full_name()}"

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"
        ordering = ['-created_at']

# --- آیتم های یک سفارش ---
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="سفارش")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="محصول")
    
    # قیمت واحد در لحظه خرید (Snapshot)
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="قیمت واحد (زمان خرید)")
    
    # مقدار: اگر کیلویی باشد (وزن)، اگر بسته‌ای باشد (تعداد)
    quantity = models.FloatField(
        validators=[MinValueValidator(0.1)], 
        verbose_name="مقدار (کیلوگرم / تعداد بسته)"
    )

    def __str__(self):
        unit = "کیلو" if self.product.sale_method == 'BY_KILO' else "بسته"
        return f"{self.product.name} ({self.quantity} {unit})"

    def get_cost(self):
        """محاسبه قیمت: مقدار * قیمت واحد"""
        if not self.price or not self.quantity:
            return 0
            
        return self.price * Decimal(str(self.quantity))

    def save(self, *args, **kwargs):
        # ذخیره قیمت لحظه‌ای محصول اگر ست نشده باشد
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)
        # آپدیت قیمت کل سفارش به محض ذخیره آیتم جدید
        self.order.calculate_total()

    class Meta:
        verbose_name = "قلم سفارش"
        verbose_name_plural = "اقلام سفارش"

# --- مدل اصلی گفتگو (تیکت) ---
class Ticket(models.Model):
    SUBJECT_CHOICES = [
        ('ORDER_TRACKING', 'پیگیری سفارش'),
        ('FEEDBACK', 'انتقاد و پیشنهاد'),
        ('COLLABORATION', 'درخواست همکاری'),
        ('OUT_OF_STOCK', 'سفارش محصول ناموجود'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'باز (در انتظار پاسخ)'),
        ('ANSWERED', 'پاسخ داده شده'),
        ('CLOSED', 'بسته شده'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets', verbose_name="کاربر")
    responder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name="پاسخ‌دهنده (مسئول)")
    
    ticket_number = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="شماره پیگیری")
    
    subject_type = models.CharField(max_length=20, choices=SUBJECT_CHOICES, verbose_name="موضوع گفتگو")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', verbose_name="وضعیت")
    
    order = models.ForeignKey('Order', on_delete=models.PROTECT, null=True, blank=True, related_name='tickets', verbose_name="سفارش مرتبط", help_text='فقط برای موضوع پیگیری سفارش')
    product = models.ForeignKey('Product', on_delete=models.PROTECT, null=True, blank=True, related_name='tickets', verbose_name="محصول مرتبط", help_text='فقط برای محصول ناموجود')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    def clean(self):
        if self.subject_type == 'ORDER_TRACKING':
            if not self.order:
                raise ValidationError({"order": "برای پیگیری سفارش، انتخاب سفارش مورد نظر الزامی است."})
            if self.order.customer != self.user:
                raise ValidationError({"order": "شما تنها می‌توانید سفارشات خود را پیگیری کنید."})

        elif self.subject_type == 'OUT_OF_STOCK':
            if not self.product:
                raise ValidationError({"product": "انتخاب محصول الزامی است."})

        if self.subject_type != 'ORDER_TRACKING':
            self.order = None
        if self.subject_type != 'OUT_OF_STOCK':
            self.product = None

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            while True:
                random_code = random.randint(100000, 999999)
                new_number = f"{random_code}"
                if not Ticket.objects.filter(ticket_number=new_number).exists():
                    self.ticket_number = new_number
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        # اضافه شدن علامت # به نمایش شماره تیکت
        return f"گفتگو #{self.ticket_number} - {self.user.get_full_name() or self.user.username}"

    class Meta:
        verbose_name = "گفتگو و پشتیبانی"
        verbose_name_plural = "گفتگوها و پشتیبانی"
        ordering = ['-updated_at']

# --- مدل پیام‌های درون گفتگو ---
class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages', verbose_name="گفتگو")
    
    # فیلد sender را blank=True کردیم تا در ادمین بتوان خالی گذاشت تا سیستم خودش پر کند
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages', verbose_name="فرستنده")
    
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name="در پاسخ به")
    text = models.TextField(verbose_name="متن پیام")
    attachment = models.FileField(
        upload_to=ticket_file_upload_path, null=True, blank=True, 
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']), validate_file_size],
        verbose_name="فایل ضمیمه", help_text="حداکثر ۵ مگابایت. فرمت: PDF, JPG, PNG,JPEG"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")

    def is_admin_reply(self):
        if self.sender.is_superuser or self.sender.is_staff :
            return True
        return False

    def clean(self):
        if self.reply_to and self.reply_to.ticket != self.ticket:
            raise ValidationError({"reply_to": "پیام ریپلای شده باید متعلق به همین گفتگو باشد."})

        # --- لاجیک اعتبارسنجی فرستنده پیام ---
        if self.sender and hasattr(self, 'ticket'):
            valid_senders = [self.ticket.user] # کاربر صاحب تیکت همیشه مجاز است
            
            if self.ticket.responder:
                valid_senders.append(self.ticket.responder) # ادمین مسئول هم مجاز است
            
            if self.sender not in valid_senders:
                # اگر ادمینی هنوز مسئول نشده (تیکت جدیده)، اولین ادمینی که جواب بده مجازه
                if not self.ticket.responder and (self.sender.is_staff or self.sender.is_superuser):
                    pass 
                else:
                    raise ValidationError({"sender": "فقط کاربر ایجاد کننده گفتگو و ادمین مسئول مجاز به ارسال پیام در این چت هستند."})

    def save(self, *args, **kwargs):

        if self.is_admin_reply():
            self.ticket.status = 'ANSWERED'
            if not self.ticket.responder:
                self.ticket.responder = self.sender
        else:
            self.ticket.status = 'OPEN'
            
        self.ticket.save()

        super().save(*args, **kwargs)

    def __str__(self):
        # بررسی اینکه اگر sender نال بود ارور ندهد
        if self.sender:
            if self.sender.is_superuser or self.sender.is_staff: 
                return f"ادمین: {self.text[:30]}"
            else:
                return f"کاربر: {self.text[:30]}"
        return f"سیستم: {self.text[:30]}"

    class Meta:
        verbose_name = "پیام"
        verbose_name_plural = "پیام‌ها"
        ordering = ['created_at']

# --- مدل لاگ های اطلاع رسانی ---
class NotificationLog(models.Model):

    class EventChoices(models.TextChoices):
        NEW_USER_TA = "NEW_USER_TA","به ادمین کاربر جدید"
        NEW_USER_TU = "NEW_USER_TU","به کاربر خوشامدگویی"

        NEW_ORDER_TA = "NEW_ORDER_TA","به ادمین سفارش جدید"
        NEW_ORDER_TU = "NEW_ORDER_TU","به کاربر سفارش ثبت شد"
        CANCELL_ORDER_TA = "CANCELL_ORDER_TA","به ادمین سفارش لغو شد"
        CANCELL_ORDER_TU = "CANCELL_ORDER_TU","به کاربر سفارش لغو شد"
        SENT_ORDER_TU = "SENT_ORDER_TU","به کاربر سفارش ارسال شد"

        NEW_TICKET_TA = "NEW_TICKET_TA","به ادمین تیکت جدید"
        NEW_TICKET_TU = "NEW_TICKET_TU","به کاربر تیکت جدید" 
        MSG_TICKET_TA = "MSG_TICKET_TA","به ادمین پیام جدید در تیکت"
        MSG_TICKET_TU = "MSG_TICKET_TU","به کاربر پیام جدید در تیکت"

        NEW_RESUMEMSG_TA = "NEW_RESUMEMSG","به ادمین پیام در رزومه"

        OTHER = "OTHER","سایر"

    
    NOTIFICATION_TYPES = [
        ('SMS', 'پیامک'),
        ('EMAIL', 'ایمیل'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'موفق'),
        ('FAILED', 'ناموفق'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications', 
        verbose_name="کاربر"
    )
    
    notification_type = models.CharField(
        max_length=10, 
        choices=NOTIFICATION_TYPES, 
        verbose_name="نوع اطلاع‌رسانی"
    )
    
    related_event = models.CharField(
       max_length=32,
       choices=EventChoices,
       verbose_name="مرتبط با رویداد",
       default="OTHER"
   ) 
    # اسنپ‌شات متن پیام
    message_content = models.TextField(verbose_name="متن پیام / اسنپ‌شات")
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='SUCCESS', 
        verbose_name="وضعیت ارسال"
    )
    
    # متن کوتاه برای دلیل خطا
    error_details = models.CharField(
        max_length=220, 
        null=True, 
        blank=True, 
        verbose_name="دلیل خطا",
        help_text="فقط در صورت ناموفق بودن ارسال پر شود."
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")

    def __str__(self):
        return f"{self.get_notification_type_display()} به {self.user} - {self.get_status_display()}" # type: ignore

    class Meta:
        verbose_name = "گزارش اطلاع‌رسانی"
        verbose_name_plural = "گزارش‌های اطلاع‌رسانی"
        ordering = ['-created_at'] # همیشه جدیدترین‌ها اول نمایش داده شوند

