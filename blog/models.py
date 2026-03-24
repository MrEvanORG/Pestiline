import os
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Max 

# وارد کردن تابع فشرده‌ساز از اپلیکیشن محصولات
from products.models import compress_image 

User = get_user_model()

# ==========================================
# توابع مسیردهی برای پوشه اختصاصی blog_photos
# ==========================================

def get_blog_category_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(f'blog_photos/categories/{instance.id or "temp"}/', filename)

def get_blog_post_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(f'blog_photos/covers/{instance.id or "temp"}/', filename)

def get_post_block_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(f'blog_photos/blocks/{instance.post.id if hasattr(instance, "post") else "temp"}/', filename)


# ==========================================
# مدل‌ها
# ==========================================

class Category(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان دسته‌بندی")
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True, verbose_name="آدرس (Slug)")
    description = models.TextField(blank=True, verbose_name="توضیحات سئو")
    
    # فیلد جدید بنر دسته‌بندی
    banner_image = models.ImageField(upload_to=get_blog_category_image_path, blank=True, null=True, verbose_name="تصویر بنر")

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def save(self, *args, **kwargs):
        # فشرده‌سازی فقط در صورت تغییر یا آپلود عکس جدید
        if self.pk:
            try:
                old_obj = Category.objects.get(pk=self.pk)
                if old_obj.banner_image != self.banner_image and self.banner_image:
                    self.banner_image = compress_image(self.banner_image, max_size_kb=400, max_width=1200)
            except Category.DoesNotExist:
                pass
        else:
            if self.banner_image:
                self.banner_image = compress_image(self.banner_image, max_size_kb=400, max_width=1200)
                
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'category_slug': self.slug})


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="نام تگ")
    slug = models.SlugField(max_length=50, unique=True, allow_unicode=True, verbose_name="آدرس تگ")

    class Meta:
        verbose_name = "تگ"
        verbose_name_plural = "تگ‌ها"

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان مقاله (H1)")
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True, verbose_name="آدرس مقاله")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts', verbose_name="دسته‌بندی")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_posts', verbose_name="نویسنده")
    
    # متادیتا و سئو
    meta_description = models.CharField(max_length=160, help_text="توضیحات کوتاه برای گوگل (حداکثر ۱۶۰ کاراکتر)", verbose_name="متا دیسکریپشن")
    short_description = models.TextField(
        blank=True, 
        verbose_name="خلاصه مقاله",
        help_text="این متن در هدر صفحه مقاله و همچنین تگ meta description برای سئو استفاده می‌شود."
    )
    reading_time = models.PositiveIntegerField(default=5, verbose_name="زمان مطالعه (دقیقه)")
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name="تگ‌ها")
    
    # تغییر مسیر آپلود عکس
    cover_image = models.ImageField(upload_to=get_blog_post_image_path, verbose_name="تصویر کاور")
    
    # فیلد جدید شمارش بازدید
    view_count = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")
    
    # وضعیت و تاریخ
    is_published = models.BooleanField(default=True, verbose_name="وضعیت انتشار")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # فشرده‌سازی فقط در صورت تغییر یا آپلود عکس جدید
        if self.pk:
            try:
                old_obj = BlogPost.objects.get(pk=self.pk)
                if old_obj.cover_image != self.cover_image and self.cover_image:
                    self.cover_image = compress_image(self.cover_image, max_size_kb=300, max_width=1000)
            except BlogPost.DoesNotExist:
                pass
        else:
            if self.cover_image:
                self.cover_image = compress_image(self.cover_image, max_size_kb=300, max_width=1000)
                
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={
            'category_slug': self.category.slug,
            'post_slug': self.slug
        })



class PostBlock(models.Model):
    post = models.ForeignKey('BlogPost', on_delete=models.CASCADE, related_name='blocks')
    block_type = models.CharField(max_length=20, choices=[
        ('h2', 'تیتر H2'), ('h3', 'تیتر H3'), ('p', 'پاراگراف'),
        ('quote', 'نقل قول'), ('image', 'تصویر تک'),
        ('gallery', 'گالری (تصویر در گرید)'), ('list', 'لیست موردی'),
        ('banner', 'بنر تبلیغاتی/CTA')
    ])
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='blog_photos/blocks/', blank=True, null=True)
    # فیلد ترتیب با مقدار پیش‌فرض بالا
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    @property
    def get_list_items(self):
        # متن را بر اساس خطوط (Enter) جدا می‌کند و خطوط خالی را حذف می‌کند
        if self.content:
            return [line.strip() for line in self.content.splitlines() if line.strip()]
        return []

    class Meta:
        ordering = ['order'] # ترتیب نمایش در دیتابیس همیشه بر اساس این فیلد باشد

    def save(self, *args, **kwargs):
        # ۱. خودکارسازی ترتیب نمایش (Order)
        if not self.pk and self.order == 0:
            max_order = PostBlock.objects.filter(post=self.post).aggregate(models.Max('order'))['order__max']
            self.order = (max_order + 1) if max_order is not None else 0

        # ۲. فشرده‌سازی هوشمند عکس
        if self.pk:
            try:
                old_obj = PostBlock.objects.get(pk=self.pk)
                if old_obj.image != self.image and self.image:
                    self.image = compress_image(self.image, max_size_kb=250, max_width=800)
            except PostBlock.DoesNotExist:
                pass
        else:
            if self.image:
                self.image = compress_image(self.image, max_size_kb=250, max_width=800)
                
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.post.title} - {self.get_block_type_display()} ({self.order})"
