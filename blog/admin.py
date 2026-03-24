from django.contrib import admin
from .models import Category, Tag, BlogPost, PostBlock
from products.admin import super_admin_site

# ==============================================================================
# کدهای آماده‌باش برای آینده (پس از دسترسی به اینترنت آزاد و نصب پکیج)
# ۱. در ترمینال بزنید: pip install django-adminsortable2
# ۲. خط زیر را از حالت کامنت (علامت #) خارج کنید:
# from adminsortable2.admin import SortableInlineAdminMixin
# ==============================================================================

@admin.register(Category, site=super_admin_site)
class CategoryAdmin(admin.ModelAdmin):
    # فیلد بنر به لیست اضافه نشده که شلوغ نشود، اما در صفحه ویرایش در دسترس است
    list_display = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Tag, site=super_admin_site)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

# ==============================================================================
# حالت فعلی اینلاین بلاک‌ها (بدون نیاز به اینترنت آزاد - عددها خودکار پر می‌شوند)
# ==============================================================================
class PostBlockInline(admin.StackedInline):
    model = PostBlock
    extra = 1
    # فیلد order را در لیست گذاشتیم تا اگر خواستید به صورت دستی شماره‌ها را تغییر دهید، بتوانید
    fields = ('block_type', 'content', 'image', 'order')
    ordering = ('order',)

# ==============================================================================
# کلاس آینده (پس از نصب پکیج، کلاس PostBlockInline بالا را کامنت کنید 
# و کلاس زیر را از کامنت درآورید تا قابلیت درگ و دراپ فعال شود)
# ==============================================================================
# class PostBlockInline(SortableInlineAdminMixin, admin.StackedInline):
#     model = PostBlock
#     extra = 1
#     fields = ('block_type', 'content', 'image') # دیگر نیازی به نمایش order نیست
# ==============================================================================

@admin.register(BlogPost, site=super_admin_site)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'reading_time', 'view_count', 'is_published', 'created_at')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'meta_description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['tags']
    inlines = [PostBlockInline]
    
    # فیلد ویو فقط برای مشاهده است و نباید دستی تغییر کند
    readonly_fields = ('view_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'slug', 'category', 'author', 'cover_image')
        }),
        ('سئو و متادیتا', {
            'fields': ('meta_description', 'tags', 'reading_time')
        }),
        ('آمار و وضعیت', {
            'fields': ('view_count', 'is_published', 'created_at', 'updated_at')
        }),
    )
