import os
import uuid
import sys
from io import BytesIO
from PIL import Image as PilImage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

# --- توابع کمکی ---

def get_file_path(instance, filename):
    """
    ذخیره فایل در پوشه: media/products_photos/{product_id}/unique_name.jpg
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    # تغییر مسیر به پوشه درخواستی شما
    return os.path.join(f'products_photos/{instance.product.id}/', filename)

def compress_image(image, max_size_kb=500):
    """فشرده‌سازی و تغییر سایز عکس"""
    im = PilImage.open(image)
    output = BytesIO()
    
    if im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    
    max_width = 1200
    if im.width > max_width:
        ratio = max_width / im.width
        new_height = int(im.height * ratio)
        im = im.resize((max_width, new_height), PilImage.Resampling.LANCZOS)

    quality = 90
    im.save(output, format='JPEG', quality=quality)
    
    while output.tell() > max_size_kb * 1024 and quality > 20:
        output.seek(0)
        output.truncate(0)
        quality -= 10
        im.save(output, format='JPEG', quality=quality)

    output.seek(0)
    
    return InMemoryUploadedFile(
        output, 
        'ImageField', 
        f"{image.name.split('.')[0]}.jpg", 
        'image/jpeg', 
        sys.getsizeof(output), 
        None
    )

# --- تنظیمات سایت ---
class SiteSettings(models.Model):
    SITE_STATUS_CHOICES = [
        ('ACTIVE', 'فعال'),
        ('MAINTENANCE', 'در حال بروزرسانی (Maintenance)'),
        ('COMING_SOON', 'بزودی (Coming Soon)'),
    ]

    status = models.CharField(max_length=15, choices=SITE_STATUS_CHOICES, default='ACTIVE', verbose_name="وضعیت سایت")
    maintenance_message = models.TextField(blank=True, null=True, verbose_name="متن صفحه غیرفعال")
    coming_soon_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ و زمان بازگشایی")
    otp_time_interval = models.PositiveIntegerField(default=120, verbose_name="زمان انتظار ارسال مجدد کد (ثانیه)")

    link_phone1 = models.CharField(max_length=100,verbose_name='لینک تماس 1',null=True,blank=True)
    link_phone2 = models.CharField(max_length=100,verbose_name='لینک تماس 2',null=True,blank=True)
    link_prphone = models.CharField(max_length=100,verbose_name='لینک شماره تماس ثابت ',null=True,blank=True)
    link_sitenumber = models.CharField(max_length=100,verbose_name='لینک شماره ارسال پیامک ثابت',null=True,blank=True)
    link_mail = models.CharField(max_length=100,verbose_name='لینک ایمیل سایت',null=True,blank=True)
    link_instagram = models.CharField(max_length=100,verbose_name='لینک اینستاگرام',null=True,blank=True)
    link_whatsapp = models.CharField(max_length=100,verbose_name='لینک واتساپ',null=True,blank=True)
    link_telegram = models.CharField(max_length=100,verbose_name='لینک تلگرام',null=True,blank=True)
    link_twitter = models.CharField(max_length=100,verbose_name='لینک توییتر',null=True,blank=True)
    link_address = models.CharField(max_length=100,verbose_name='لینک آدرس',null=True,blank=True)
    address_text = models.CharField(max_length=100,verbose_name='متن آدرس',null=True,blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("فقط یک تنظیمات کلی برای سایت می‌تواند وجود داشته باشد.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return "تنظیمات عمومی پستیلاین"

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

# --- مدل‌های پایه (استان و شهر) ---
class Province(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام استان")
    def __str__(self): return self.name
    class Meta: verbose_name = "استان"; verbose_name_plural = "استان‌ها"

class City(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities', verbose_name="استان")
    name = models.CharField(max_length=100, verbose_name="نام شهر")
    def __str__(self): return f"{self.name} ({self.province.name})"
    class Meta: verbose_name = "شهر"; verbose_name_plural = "شهرها"

# --- مدل کاربر ---
class User(AbstractUser):
    phone_regex = RegexValidator(regex=r'^09\d{9}$', message="شماره موبایل باید ۱۱ رقم بوده و با ۰۹ شروع شود.")
    phone_number = models.CharField(validators=[phone_regex], max_length=11, unique=True, verbose_name="شماره همراه")
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="استان")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="شهر")

    def clean(self):
        super().clean()
        if self.province and self.city and self.city.province != self.province:
            raise ValidationError({'city': f"شهر '{self.city.name}' متعلق به استان '{self.province.name}' نیست."})

    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']
    
    def __str__(self): return f"{self.get_full_name()} ({self.phone_number})"
    class Meta: verbose_name = "کاربر"; verbose_name_plural = "کاربران"

# --- مدل محصول ---
class Product(models.Model):
    PISTACHIO_TYPES = [('AKBARI', 'اکبری'), ('FANDOGHI', 'فندقی'), ('AHMAD_AGHAEI', 'احمدآقایی'), ('KALEH_GHOOCHI', 'کله قوچی')]
    SALE_METHODS = [('PACKAGED', 'بسته‌ای'), ('BY_KILO', 'کیلویی')]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', verbose_name="فروشنده")
    name = models.CharField(max_length=255, verbose_name="نام محصول")
    sale_method = models.CharField(max_length=20, choices=SALE_METHODS, verbose_name="نوع فروش")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="قیمت (تومان)")
    package_weight = models.FloatField(null=True, blank=True, verbose_name="وزن هر بسته (کیلو)")
    stock = models.FloatField(verbose_name="موجودی")
    min_order = models.FloatField(default=1, verbose_name="کف سفارش")
    max_order = models.FloatField(default=100, verbose_name="سقف سفارش")
    is_mixed = models.BooleanField(default=False, verbose_name="آیا محصول ترکیبی است؟")

    def clean(self):
        if self.sale_method == 'PACKAGED' and not self.package_weight:
            raise ValidationError("برای فروش بسته‌ای، وارد کردن وزن هر بسته الزامی است.")

    def __str__(self): return self.name
    class Meta: verbose_name = "محصول"; verbose_name_plural = "محصولات"

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

# ... (کدهای قبلی مدل Product و ... )

# --- ۶. مدل‌های سفارش (Order System) ---
from decimal import Decimal

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار پرداخت'),
        ('PROCESSING', 'در حال پردازش (تایید پرداخت)'),
        ('SHIPPED', 'ارسال شده'),
        ('DELIVERED', 'تحویل شده'),
        ('CANCELED', 'لغو شده'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="مشتری")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="وضعیت")
    
    # اطلاعات گیرنده (بدون شهر و استان طبق درخواست)
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
    tracking_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="کد پیگیری پستی")

    def __str__(self):
        return f"سفارش #{self.id} - {self.customer.get_full_name()}"

    def calculate_total(self):
        """محاسبه مجدد قیمت کل سفارش"""
        items_total = sum(item.get_cost() for item in self.items.all())
        shipping = self.shipping_cost if self.shipping_cost else 0
        self.total_price = items_total + shipping
        self.save()

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"
        ordering = ['-created_at']


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
        """
        محاسبه قیمت: مقدار * قیمت واحد
        """
        # اصلاح باگ: اگر قیمت یا مقدار هنوز وارد نشده (مثل ردیف‌های خالی در ادمین)، صفر برگردان
        if not self.price or not self.quantity:
            return 0
            
        return self.price * Decimal(str(self.quantity))

    def save(self, *args, **kwargs):
        # ذخیره قیمت لحظه‌ای محصول اگر ست نشده باشد
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)
        # آپدیت قیمت کل سفارش
        self.order.calculate_total()

    class Meta:
        verbose_name = "قلم سفارش"
        verbose_name_plural = "اقلام سفارش"