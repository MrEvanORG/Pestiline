from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import StaticPageSEO
from products.models import Product
from resume.models import Resume
from blog.models import BlogPost , Category

class StaticViewSitemap(Sitemap):
    def get_seo_settings(self):
        seo, _ = StaticPageSEO.objects.get_or_create()
        return seo

    def items(self):
        seo = self.get_seo_settings()
        mapping = {
            'index': seo.home_status,
            'shop': seo.shop_status,
            'blog:blog_index': seo.blog_status,
            'mixer': seo.mixer_status,
            'ai_assistant': seo.ai_status,
            'about_us': seo.about_status,  
        }
        return [name for name, enabled in mapping.items() if enabled]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        seo = self.get_seo_settings()
        mapping = {
            'index': seo.home_priority,
            'shop': seo.shop_priority,
            'blog:blog_index': seo.blog_priority,
            'mixer': seo.mixer_priority,
            'ai_assistant': seo.ai_priority,
            'about_us': seo.about_priority,
        }
        return float(mapping.get(item, 0.5))

    def changefreq(self, item):
        seo = self.get_seo_settings()
        mapping = {
            'index': seo.home_changefreq,
            'shop': seo.shop_changefreq,
            'blog:blog_index': seo.blog_changefreq,
            'mixer': seo.mixer_changefreq,
            'ai_assistant': seo.ai_changefreq,
            'about_us': seo.about_changefreq,
        }
        return mapping.get(item, 'monthly')
    
class ProductSitemap(Sitemap):
    changefreq = "monthly"   # پیش‌فرض اگر فیلد خالی بود
    priority = 0.8

    def items(self):
        # فقط محصولاتی که فعال هستند و موجودی دارند
        return Product.objects.filter(active_status=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('product_detail', kwargs={'slug': obj.slug})

    def changefreq(self, obj):
        # از فیلد مدل
        return obj.changefreq or "monthly"

    def priority(self, obj):
        return float(obj.seo_priority or 0.8)
    
class BlogPostSitemap(Sitemap):
    changefreq = "monthly" 
    priority = 0.7

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def priority(self, obj):
        return float(obj.seo_priority or priority)

    def changefreq(self, obj):
        return obj.changefreq or changefreq

    def location(self, obj):
        return obj.get_absolute_url()

class CategorySitemap(Sitemap):
    changefreq = "weekly"
    seo_priority = 0.7

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()

    def priority(self, obj):
        return float(obj.seo_priority or seo_priority)
    
    def changefreq(self, obj):
        return (obj.changefreq or changefreq)

class ResumeSitemap(Sitemap):
    def items(self):
        return Resume.objects.filter(is_confirmed=True)

    def priority(self, obj):
        return float(obj.seo_priority)

    def changefreq(self, obj):
        return obj.changefreq
    


# --- برای صفحات داینامیک ---
# کلاس‌های داینامیک را مشابه نمونه قبلی ایجاد کنید. به عنوان مثال:
# class ProductSitemap(Sitemap):
#     def items(self): return Product.objects.all()
#     def priority(self, obj): return float(obj.seo_priority)
#     def changefreq(self, obj): return obj.changefreq



# ۱. صفحات استاتیک (Static Views)
# صفحه خانه (Home):
# Priority: 
# 1.0
# 1.0
#  (مهم‌ترین صفحه سایت)
# Changefreq: daily (چون مقالات، محصولات جدید و فیچرها مدام در آن آپدیت می‌شوند)
# صفحه فروشگاه (Shop Index):
# Priority: 
# 0.9
# 0.9
#  (صفحه اصلی درآمدزایی و لندینگ پیج مهم)
# Changefreq: daily (با اضافه شدن محصولات جدید یا تغییر موجودی مدام تغییر می‌کند)
# صفحه اصلی وبلاگ (Blog Index):
# Priority: 
# 0.8
# 0.8
# Changefreq: daily یا weekly (بستگی به سرعت تولید محتوای شما دارد)
# بخش میکسر (Mixer):
# Priority: 
# 0.8
# 0.8
#  (یک فیچر جذاب و یونیک برای فروش که ارزش سئویی بالایی دارد)
# Changefreq: monthly (ظاهر و عملکرد این صفحه معمولا ثابت است)
# بخش AI (راهنمای خرید):
# Priority: 
# 0.7
# 0.7
#  (فیچر مفیدی است اما لندینگ اصلی نیست)
# Changefreq: monthly (سوالات درختی و منطق آن کمتر تغییر می‌کند)
# صفحه درباره ما (About Us):
# Priority: 
# 0.5
# 0.5
# Changefreq: monthly یا yearly (اطلاعات برند به ندرت تغییر می‌کند)


# ۲. صفحات جزییات پویا (Dynamic Detail Views)
# صفحه جزییات محصول (Product Detail):
# Priority: 
# 0.8
# 0.8
#  (دیفالت)
# Changefreq: weekly (به خاطر تغییرات قیمت، موجودی و ثبت نظرات جدید کاربران)
# صفحه جزییات کتگوری (Category Detail):
# Priority: 
# 0.7
# 0.7
#  (دیفالت)
# Changefreq: weekly (با اضافه شدن محصولات یا مقالات جدید به دسته‌بندی تغییر می‌کند)
# صفحه پست وبلاگ (Blog Post):
# Priority: 
# 0.7
# 0.7
#  (دیفالت)
# Changefreq: monthly (محتوای مقاله معمولاً ثابت است، مگر با ثبت کامنت جدید)
# صفحه رزومه کارمندان (Employee Resume):
# Priority: 
# 0.3
# 0.3
#  (دیفالت - ارزش سئویی پایینی برای جذب مشتری دارد)
# Changefreq: yearly (به ندرت تغییر می‌کند)