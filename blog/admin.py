from django.contrib import admin
from django.utils.html import format_html
from products.admin import super_admin_site
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from .models import Category, Tag, BlogPost, PostBlock
from products.templatetags.custom_filters import to_jalali
from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin

User = get_user_model()

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

class PostBlockInline(SortableInlineAdminMixin, admin.StackedInline):
    model = PostBlock
    extra = 1
    fields = ('block_type', 'content', 'image', 'image_preview', 'order')
    ordering = ('order',)
    readonly_fields = ('image_preview',)
    class Media:
        js = ('blog/js/admin_postblock.js',)

    def image_preview(self, obj):
        if obj and obj.image:
            # اینجا چون متغیر {obj.image.url} داریم، format_html درست است
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 5px;" />', obj.image.url)
        
        # اینجا چون هیچ متغیری نداریم و فقط یک رشته ثابت است، از mark_safe استفاده می‌کنیم
        return mark_safe('<script>document.currentScript.closest(".form-row").style.display="none";</script>')
        
    image_preview.short_description = "پیش‌نمایش"


# ==============================================================================
# کلاس آینده (پس از نصب پکیج، کلاس PostBlockInline بالا را کامنت کنید 
# و کلاس زیر را از کامنت درآورید تا قابلیت درگ و دراپ فعال شود)
# ==============================================================================
# class PostBlockInline(SortableInlineAdminMixin, admin.StackedInline):
#     model = PostBlock
#     extra = 1
#     fields = ('block_type', 'content', 'image') # دیگر نیازی به نمایش order نیست
# ==============================================================================
class AuthorFilter(admin.SimpleListFilter): #create cuatom floor filter
    title = 'نویسنده'
    parameter_name = 'author'

    def lookups(self, request, model_admin):
        floors = sorted(set(User.objects.values_list('floor_n', flat=True)))
        return [(f, f"طبقه {f}") for f in floors]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(floor_number=self.value())
        return queryset
    
@admin.register(BlogPost, site=super_admin_site)
class BlogPostAdmin(SortableAdminBase,admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'view_count', 'is_published', 'tj_created_at')
    list_filter = ('is_published', 'category', 'created_at','author')
    search_fields = ('title', 'meta_description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['tags']
    inlines = [PostBlockInline]
    
    # فیلد ویو فقط برای مشاهده است و نباید دستی تغییر کند
    readonly_fields = ('view_count', 'tj_created_at', 'tj_updated_at','cover_image_preview')

    def cover_image_preview(self, obj):
        if obj and obj.cover_image:
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 5px;" />', obj.cover_image.url)
    
        return mark_safe('<script>document.currentScript.closest(".form-row").style.display="none";</script>')
    
    cover_image_preview.short_description = "پیش‌نمایش"
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('slug', 'is_published', 'seo_priority','changefreq','view_count')
        }),
        ('اطلاعات اصلی', {
            'fields': ('title', 'category', 'author', 'cover_image','cover_image_preview','cover_image_alt')
        }),
        ('سئو و متادیتا', {
            'fields': ('meta_description', 'tags', 'reading_time')
        }),
        ('آمار و وضعیت', {
            'fields': ( 'tj_created_at', 'tj_updated_at')
        }),
    )


    def tj_created_at(self,obj):
        return to_jalali(obj.created_at,form="persian_date_time")
    tj_created_at.short_description = "تاریخ ایجاد"

    def tj_updated_at(self,obj):
        return to_jalali(obj.updated_at,form="persian_date_time")
    tj_updated_at.short_description = "تاریخ بروزرسانی"
