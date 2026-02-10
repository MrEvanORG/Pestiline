from .addons import persian_slugify
from django.utils.text import slugify
from django.urls import reverse
from django.db import models
import os 

def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext

def upload_image_path(instance, filename):
    name, ext = get_filename_ext(filename)
    slug_name = instance.slug if instance.slug else slugify(instance.name, allow_unicode=True)
    final_name = f"{slug_name}{ext}"
    return f"avatars/{final_name}"

class Resume(models.Model):

    class RoleType(models.TextChoices):
        developer = "developer","توسعه دهنده"
        accountant = "accountant","حسابدار"
        content_manager = "content_manager","مدیر محتوا"
        seo_manager = "seo_manager","مدیر سئو"
        ui_designer = "ui_designer","طراح Ux"
        ux_designer = "ux_designer","طراح Ui"
        uxui_designer = "uxui_designer","طراح Ui/Ux"
        sql_designer = "sql_designer","طراح پایگاه داده"

    slug = models.SlugField(allow_unicode=True,unique=True, blank=True,verbose_name='اسلاگ رزومه')
    role = models.CharField(max_length=20,choices=RoleType,default=RoleType.developer,verbose_name='نقش')
    is_confirmed = models.BooleanField(default=False,verbose_name='وضعیت نمایش')
    name = models.CharField(max_length=100, verbose_name="نام")
    title = models.CharField(max_length=100, verbose_name="تخصص کوتاه (مثلا: برنامه‌نویس وب)")
    avatar = models.ImageField(upload_to=upload_image_path, verbose_name="تصویر آواتار", help_text="بهترین اندازه: 200x200 پیکسل")
    about_me = models.TextField(verbose_name="درباره من (معرفی کوتاه)")
    age = models.PositiveIntegerField(verbose_name="سن")
    email = models.EmailField(verbose_name="ایمیل")
    phone_number = models.CharField(max_length=20, verbose_name="شماره همراه")
    address = models.CharField(max_length=255, verbose_name="آدرس")
    resume_file = models.FileField(upload_to='resumes/', verbose_name="فایل رزومه (PDF)", null=True, blank=True)

    skills_category_1 = models.TextField(
        verbose_name="مهارت‌های دسته اول (فنی)",
        help_text='مهارت‌ها را به فرمت "نام,درصد" وارد کنید و با ; جدا نمایید. مثال: HTML,95;CSS,40'
    )
    skills_category_2 = models.TextField(
        verbose_name="مهارت‌های دسته دوم (نرم‌افزار)",
        help_text='مثال: Adobe Photoshop,80;Sketch,85'
    )


    twitter_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="لینک توییتر")
    telegram_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="لینک تلگرام")
    instagram_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="لینک اینستاگرام")
    github_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="لینک گیت‌هاب")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "رزومه"
        verbose_name_plural = "رزومه‌ها"
    def get_absolute_url(self):
        return reverse("resume_detail",args=[self.slug])
    

    def save(self,*args,**kwargs):
        if not self.slug :
            self.slug = persian_slugify(self.name)
        super().save(*args,**kwargs)

class WorkExperience(models.Model):
    resume = models.ForeignKey(Resume, related_name='work_experiences', on_delete=models.CASCADE)
    position = models.CharField(max_length=100, verbose_name="سمت شغلی")
    company = models.CharField(max_length=100, verbose_name="محل انجام کار (شرکت)")
    web_link = models.URLField(verbose_name="لینک وبسایت ارائه شده",null=True,blank=True)
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

