from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class ChangeFreqChoices(models.TextChoices):
    ALWAYS = 'always', 'Always'
    HOURLY = 'hourly', 'Hourly'
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'
    YEARLY = 'yearly', 'Yearly'
    NEVER = 'never', 'Never'

class StaticPageSEO(models.Model):

    # --- Home ---
    home_status = models.BooleanField(default=True,verbose_name='انتشار خانه در سایت مپ')
    home_changefreq = models.CharField(max_length=20, choices=ChangeFreqChoices.choices, default=ChangeFreqChoices.WEEKLY)
    home_priority = models.DecimalField(max_digits=2, decimal_places=1, default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    # --- Shop ---
    shop_status = models.BooleanField(default=False,verbose_name='انتشار صفحه فروشگاه در سایت مپ')
    shop_changefreq = models.CharField(max_length=20, choices=ChangeFreqChoices.choices, default=ChangeFreqChoices.DAILY)
    shop_priority = models.DecimalField(max_digits=2, decimal_places=1, default=0.9, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    # --- Blog Index ---
    blog_status = models.BooleanField(default=True,verbose_name='انتشار صفحه ایندکس وبلاگ در سایت مپ')
    blog_changefreq = models.CharField(max_length=20, choices=ChangeFreqChoices.choices, default=ChangeFreqChoices.WEEKLY)
    blog_priority = models.DecimalField(max_digits=2, decimal_places=1, default=0.8, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    # --- Mixer ---
    mixer_status = models.BooleanField(default=False,verbose_name='انتشار صفحه میکسر در سایت مپ')
    mixer_changefreq = models.CharField(max_length=20, choices=ChangeFreqChoices.choices, default=ChangeFreqChoices.MONTHLY)
    mixer_priority = models.DecimalField(max_digits=2, decimal_places=1, default=0.7, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    # --- AI Assistant ---
    ai_status = models.BooleanField(default=False,verbose_name='انتشار صفحه Ai در سایت مپ')
    ai_changefreq = models.CharField(max_length=20, choices=ChangeFreqChoices.choices, default=ChangeFreqChoices.MONTHLY)
    ai_priority = models.DecimalField(max_digits=2, decimal_places=1, default=0.8, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    # --- About Us ---
    about_status = models.BooleanField(default=False,verbose_name='انتشار صفحه درباره ما در سایت مپ')
    about_changefreq = models.CharField(max_length=20, choices=ChangeFreqChoices.choices, default=ChangeFreqChoices.MONTHLY)
    about_priority = models.DecimalField(max_digits=2, decimal_places=1, default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    class Meta:
        verbose_name = 'تنظیمات سئو صفحات استاتیک'
        verbose_name_plural = 'تنظیمات سئو صفحات استاتیک'

    def __str__(self):
        return "تنظیمات سایت‌ مپ استاتیک"

class CustomSeoData(models.Model):
    path = models.CharField(max_length=220,unique=True,verbose_name='مسیر صفحه',help_text='مثال : /about_us/')
    title = models.CharField(max_length=60,null=True,blank=True,verbose_name='تایتل صفحه',help_text='حداکثر 60 کاراکتر')
    meta_description = models.CharField(max_length=160,null=True,blank=True,verbose_name='توضیحات صفحه',help_text='حداکثر 160 کاراکتر\nدر صورت وارد نکردن این فیلد توضیحات پیشفرض صفحه نمایش داده خواهند شد.')
    
    def __str__(self):
        return f"عنوان و توضیحات سفارشی برای {self.path}"
    class Meta:
        verbose_name = "عنوان سفارسی"
        verbose_name_plural = "عناوین و توضیحات سفارشی"
