import os
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from products.models import User
from seo.models import ChangeFreqChoices
from django.core.validators import MinValueValidator, MaxValueValidator
# ایمپورت تابع فشرده‌سازی از محصولات
from products.models import compress_image 
from .addons import persian_slugify


def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext

def upload_image_path(instance, filename):
    name, ext = get_filename_ext(filename)
    slug_name = instance.slug if instance.slug else slugify(instance.name, allow_unicode=True)
    final_name = f"{slug_name}{ext}"
    # تغییر مسیر به پوشه مورد نظر شما
    return f"avatars_photo/{final_name}"

# ولیدیتور برای محدودیت ۲ مگابایتی فایل
def validate_file_size(value):
    filesize = value.size
    if filesize > 2 * 1024 * 1024:  # 2 MB
        raise ValidationError("حداکثر حجم مجاز برای فایل رزومه ۲ مگابایت است.")


class Resume(models.Model):

    class RoleType(models.TextChoices):
        developer = "developer", "توسعه دهنده"
        accountant = "accountant", "حسابدار"
        content_manager = "content_manager", "مدیر محتوا"
        seo_manager = "seo_manager", "مدیر سئو"
        ui_designer = "ui_designer", "طراح Ux"
        ux_designer = "ux_designer", "طراح Ui"
        uxui_designer = "uxui_designer", "طراح Ui/Ux"
        sql_designer = "sql_designer", "طراح پایگاه داده"

    is_confirmed = models.BooleanField(default=True, verbose_name='وضعیت نمایش و انتشار در سایت مپ')
    
    seo_priority = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        default=0.4,  # <--- مقدار جدید
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='اولویت سئو'
    )
    changefreq = models.CharField(
        max_length=20, 
        choices=ChangeFreqChoices.choices, 
        default=ChangeFreqChoices.MONTHLY,  # <--- مقدار جدید
        verbose_name='فرکانس تغییر'
    )
    slug = models.SlugField(allow_unicode=True, unique=True, blank=True, verbose_name='اسلاگ رزومه')
    related_user = models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL,verbose_name='مرتبط با کاربر')
    role = models.CharField(max_length=20, choices=RoleType, default=RoleType.developer, verbose_name='نقش')

    # تغییر دیفالت فرکانس تغییر برای محصول به WEEKLY
    name = models.CharField(max_length=100, verbose_name="نام")
    title = models.CharField(max_length=100, verbose_name="تخصص کوتاه (مثلا: برنامه‌نویس وب)")
    
    # استفاده از upload_image_path جدید
    avatar = models.ImageField(upload_to=upload_image_path, verbose_name="تصویر آواتار", help_text="بهترین اندازه: 200x200 پیکسل")
    about_me = models.TextField(verbose_name="درباره من (معرفی کوتاه)")
    age = models.PositiveIntegerField(verbose_name="سن")
    email = models.EmailField(verbose_name="ایمیل")
    phone_number = models.CharField(max_length=20, verbose_name="شماره همراه")
    address = models.CharField(max_length=220, verbose_name="آدرس")
    
    # اضافه شدن validator برای محدودیت حجم
    resume_file = models.FileField(upload_to='resumes/', validators=[validate_file_size], verbose_name="فایل رزومه (PDF)", null=True, blank=True)

    skills_category_1 = models.TextField(
        verbose_name="مهارت‌های دسته اول (فنی)",
        help_text='مهارت‌ها را به فرمت "نام,درصد" وارد کنید و با ; جدا نمایید. مثال: HTML,95; CSS,40;'
    )
    skills_category_2 = models.TextField(
        verbose_name="مهارت‌های دسته دوم (نرم‌افزار)",
        help_text='مثال: Adobe Photoshop,80; figma,85; Adobe XD,20'
    )

    twitter_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="لینک توییتر")
    telegram_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="لینک تلگرام")
    instagram_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="لینک اینستاگرام")
    github_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="لینک گیت‌هاب")

    visit_count = models.PositiveIntegerField(default=0,verbose_name='تعداد بازدید')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "رزومه"
        verbose_name_plural = "رزومه‌ها"

    def get_absolute_url(self):
        return reverse("resume_detail", args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = persian_slugify(self.name)
            
        if self.avatar:
            if not self.pk: 
                self.avatar = compress_image(self.avatar)
            else: 
                try:
                    old = Resume.objects.get(pk=self.pk)
                    if self.avatar.name != old.avatar.name: 
                        self.avatar = compress_image(self.avatar)
                except Resume.DoesNotExist:
                    pass

        super().save(*args, **kwargs)
# مدل‌های WorkExperience و Education تغییر نکردند (همان کدهای خودتان را نگه دارید)
class WorkExperience(models.Model):
    resume = models.ForeignKey(Resume, related_name='work_experiences', on_delete=models.CASCADE)
    position = models.CharField(max_length=100, verbose_name="سمت شغلی")
    company = models.CharField(max_length=100, verbose_name="محل انجام کار (شرکت)")
    web_link = models.URLField(verbose_name="لینک وبسایت ارائه شده", null=True, blank=True)
    period = models.CharField(max_length=100, verbose_name="بازه زمانی (مثال: May, 2015 - Present)")
    description = models.TextField(verbose_name="توضیحات و تجربیات")

    def __str__(self):
        return f"{self.position} در {self.company}"

    class Meta:
        verbose_name = "سابقه کاری"
        verbose_name_plural = "سوابق کاری"
        ordering = ['-id']

class Education(models.Model):
    resume = models.ForeignKey(Resume, related_name='educations', on_delete=models.CASCADE)
    degree = models.CharField(max_length=100, verbose_name="مدرک تحصیلی")
    institution = models.CharField(max_length=100, verbose_name="محل تحصیل (دانشگاه)")
    period = models.CharField(max_length=100, verbose_name="بازه زمانی (مثال: 2011 - 2013)")
    description = models.TextField(verbose_name="توضیحات")

    def __str__(self):
        return f"{self.degree} از {self.institution}"

    class Meta:
        verbose_name = "سابقه تحصیلی"
        verbose_name_plural = "سوابق تحصیلی"
        ordering = ['-id']