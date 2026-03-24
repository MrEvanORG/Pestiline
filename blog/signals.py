import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Category, BlogPost, PostBlock

# ==========================================
# سیگنال‌های Category (بنر دسته‌بندی)
# ==========================================
@receiver(post_delete, sender=Category)
def delete_category_banner_file(sender, instance, **kwargs):
    if instance.banner_image and os.path.isfile(instance.banner_image.path):
        try:
            os.remove(instance.banner_image.path)
        except PermissionError:
            pass

@receiver(pre_save, sender=Category)
def delete_old_category_banner_on_update(sender, instance, **kwargs):
    if not instance.pk: return False
    try:
        old_file = sender.objects.get(pk=instance.pk).banner_image
    except sender.DoesNotExist:
        return False
    new_file = instance.banner_image
    if old_file and old_file != new_file and os.path.isfile(old_file.path):
        try:
            os.remove(old_file.path)
        except PermissionError:
            pass

# ==========================================
# سیگنال‌های BlogPost (کاور مقاله)
# ==========================================
@receiver(post_delete, sender=BlogPost)
def delete_blog_post_image_file(sender, instance, **kwargs):
    if instance.cover_image and os.path.isfile(instance.cover_image.path):
        try:
            os.remove(instance.cover_image.path)
        except PermissionError:
            pass

@receiver(pre_save, sender=BlogPost)
def delete_old_post_image_on_update(sender, instance, **kwargs):
    if not instance.pk: return False
    try:
        old_file = sender.objects.get(pk=instance.pk).cover_image
    except sender.DoesNotExist:
        return False
    new_file = instance.cover_image
    if old_file and old_file != new_file and os.path.isfile(old_file.path):
        try:
            os.remove(old_file.path)
        except PermissionError:
            pass
# ==========================================
# سیگنال‌های PostBlock (عکس‌های داخل مقاله)
# ==========================================
@receiver(post_delete, sender=PostBlock)
def delete_post_block_image_file(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        try:
            os.remove(instance.image.path)
        except PermissionError:
            pass

@receiver(pre_save, sender=PostBlock)
def delete_old_post_block_image_on_update(sender, instance, **kwargs):
    if not instance.pk: return False
    try:
        old_file = sender.objects.get(pk=instance.pk).image
    except sender.DoesNotExist:
        return False
    new_file = instance.image
    if old_file and old_file != new_file and os.path.isfile(old_file.path):
        try:
            os.remove(old_file.path)
        except PermissionError:
            pass
        # در ویندوز اگر فایل موقتاً درگیر باشد، از حذف آن چشم‌پوشی می‌کنیم

