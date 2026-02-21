import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Resume

@receiver(post_delete, sender=Resume)
def delete_resume_files(sender, instance, **kwargs):
    """
    وقتی رکورد رزومه حذف می‌شود، آواتار و فایل PDF از هاست پاک شوند.
    """
    # پاک کردن آواتار
    if instance.avatar and os.path.isfile(instance.avatar.path):
        os.remove(instance.avatar.path)
        
    # پاک کردن فایل PDF
    if instance.resume_file and os.path.isfile(instance.resume_file.path):
        os.remove(instance.resume_file.path)

@receiver(pre_save, sender=Resume)
def delete_old_resume_files_on_update(sender, instance, **kwargs):
    """
    وقتی رزومه ادیت شده و عکس یا PDF جدیدی جایگزین می‌شود، فایل‌های قدیمی پاک شوند.
    """
    if not instance.pk:
        return False

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return False

    # بررسی آپدیت عکس آواتار
    if old_instance.avatar and old_instance.avatar != instance.avatar:
        if os.path.isfile(old_instance.avatar.path):
            os.remove(old_instance.avatar.path)

    # بررسی آپدیت فایل رزومه (PDF)
    if old_instance.resume_file and old_instance.resume_file != instance.resume_file:
        if os.path.isfile(old_instance.resume_file.path):
            os.remove(old_instance.resume_file.path)