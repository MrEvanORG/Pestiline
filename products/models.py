from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class SiteSettings(models.Model):
    SITE_STATUS_CHOICES = [
        ('ACTIVE', 'فعال'),
        ('MAINTENANCE', 'در حال بروزرسانی (Maintenance)'),
        ('COMING_SOON', 'بزودی (Coming Soon)'),
    ]

    status = models.CharField(
        max_length=15, 
        choices=SITE_STATUS_CHOICES, 
        default='ACTIVE',
        verbose_name="وضعیت سایت"
    )
    maintenance_message = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="متن صفحه غیرفعال",
        help_text="پیامی که در زمان غیرفعال بودن سایت به کاربر نمایش داده می‌شود."
    )
    coming_soon_date = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="تاریخ و زمان بازگشایی",
        help_text="اگر وضعیت روی 'بزودی' است، این تاریخ را پر کنید."
    )

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

    @property
    def is_time_up(self):
        if self.coming_soon_date:
            return timezone.now() >= self.coming_soon_date
        return False

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("فقط یک تنظیمات کلی برای سایت می‌تواند وجود داشته باشد.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return "تنظیمات عمومی پستیلاین"

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"


class User(AbstractUser):
    first_name = models.CharField(max_length=20, verbose_name='نام')
    last_name = models.CharField(max_length=20, verbose_name='نام خانوادگی')

    def is_pestiline_seller(self):
        return self.is_superuser

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({'پستیلاین' if self.is_superuser else 'فروشنده'})"


# --- ۲. مدل اصلی محصول پستیلاین ---
class Product(models.Model):
    PISTACHIO_TYPES = [
        ('AKBARI', 'اکبری'),
        ('FANDOGHI', 'فندقی'),
        ('AHMAD_AGHAEI', 'احمدآقایی'),
        ('KALEH_GHOOCHI', 'کله قوچی'),
    ]

    SALE_METHODS = [
        ('PACKAGED', 'بسته‌ای'),
        ('BY_KILO', 'کیلویی'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', verbose_name="فروشنده")
    name = models.CharField(max_length=255, verbose_name="نام محصول")
    
    # تنظیمات فروش
    sale_method = models.CharField(max_length=20, choices=SALE_METHODS, verbose_name="نوع فروش")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="قیمت (تومان)")
    
    # فیلدهای مربوط به بسته‌ای
    package_weight = models.FloatField(null=True, blank=True, verbose_name="وزن هر بسته (کیلو)")
    
    # فیلدهای موجودی و محدودیت سفارش
    stock = models.FloatField(verbose_name="موجودی (تعداد بسته یا کیلوگرم)")
    min_order = models.FloatField(default=1, verbose_name="کف سفارش")
    max_order = models.FloatField(default=100, verbose_name="سقف سفارش")

    # فیلد تشخیص ترکیبی بودن
    is_mixed = models.BooleanField(default=False, verbose_name="آیا محصول ترکیبی است؟")

    def clean(self):
        if self.sale_method == 'PACKAGED' and not self.package_weight:
            raise ValidationError("برای فروش بسته‌ای، وارد کردن وزن هر بسته الزامی است.")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"


# --- ۳. مدل اجزای تشکیل‌دهنده (نوع خاص پسته) ---
class ProductComponent(models.Model):
    PROCESSING_CHOICES = [('RAW', 'خام'), ('ROASTED', 'شور/بو داده')]
    SHELL_CHOICES = [('OPEN', 'خندان'), ('CLOSED', 'دهن‌ بست')]
    QUALITY_CHOICES = [('LUXARY','دستچین / اعلاء'),('STANDARD','استاندارد / معمولی') ,('ECONOMY','اقتصادی')]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='components')
    pistachio_type = models.CharField(max_length=20, choices=Product.PISTACHIO_TYPES, verbose_name="نوع پسته")
    processing = models.CharField(max_length=10, choices=PROCESSING_CHOICES, verbose_name="فرآوری")
    shell_status = models.CharField(max_length=10, choices=SHELL_CHOICES, verbose_name="وضعیت دهان")
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, verbose_name='کیفیت', null=True)
    
    percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="درصد تشکیل‌دهنده"
    )

    def __str__(self):
        return f"نوع خاص {self.pk if self.pk else ''}"

    class Meta:
        verbose_name = "نوع خاص پسته"
        verbose_name_plural = "نوع خاص پسته"