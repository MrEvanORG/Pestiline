import os
from django.db.models.signals import post_delete, pre_save , post_save
from django.dispatch import receiver
from .models import ProductImage , Order , User , TicketMessage , SiteSettings
# ---------------------------------------------------------
# سیگنال‌های مربوط به حذف عکس محصولات 
# ---------------------------------------------------------
@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    """
    وقتی رکورد عکس از دیتابیس حذف می‌شود، فایل آن هم از هاست پاک شود.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

@receiver(pre_save, sender=ProductImage)
def delete_old_image_on_update(sender, instance, **kwargs):
    """
    وقتی عکس جایگزین می‌شود، عکس قبلی پاک شود.
    """
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).image
    except sender.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

# ---------------------------------------------------------
# سیگنال‌های مربوط به حذف فایل‌های ضمیمه تیکت‌های پشتیبانی
# ---------------------------------------------------------
@receiver(post_delete, sender=TicketMessage)
def delete_ticket_message_attachment(sender, instance, **kwargs):
    """
    وقتی پیام تیکت از دیتابیس حذف می‌شود، فایل ضمیمه آن هم از هاست پاک شود.
    """
    if instance.attachment:
        if os.path.isfile(instance.attachment.path):
            os.remove(instance.attachment.path)

@receiver(pre_save, sender=TicketMessage)
def delete_old_attachment_on_update(sender, instance, **kwargs):
    """
    وقتی فایل ضمیمه در یک پیام ویرایش یا جایگزین می‌شود، فایل قبلی از هاست پاک شود.
    """
    # اگر پیام جدید است و هنوز در دیتابیس ذخیره نشده، نیازی به بررسی نیست
    if not instance.pk:
        return False

    try:
        # واکشی فایل قدیمی از دیتابیس
        old_file = sender.objects.get(pk=instance.pk).attachment
    except sender.DoesNotExist:
        return False

    new_file = instance.attachment
    
    # اگر فایل قدیمی وجود داشت و با فایل جدید تفاوت داشت، آن را حذف کن
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

# ---------------------------------------------------------
# سیگنال‌های مربوط به حذف فایل ولکام سانگ
# --------------------------------------------------------
@receiver(post_delete, sender=SiteSettings)
def delete_welcome_song_on_delete(sender, instance, **kwargs):
    if instance.welcome_song:
        instance.welcome_song.delete(save=False)

@receiver(pre_save, sender=SiteSettings)
def delete_old_welcome_song_on_update(sender, instance, **kwargs):

    if not instance.pk:
        return

    try:
        old_instance = SiteSettings.objects.get(pk=instance.pk)
    except SiteSettings.DoesNotExist:
        return

    if old_instance.welcome_song and old_instance.welcome_song != instance.welcome_song:
        old_instance.welcome_song.delete(save=False)

# ---------------------------------------------------------
# سیگنال‌های ایجاد کاربر جدید
# --------------------------------------------------------
@receiver(post_save, sender=User)
def handle_new_user_registration(sender, instance, created, **kwargs):
    from .notifications import notify_new_user_welcome, notify_admins_new_user
    if created:
        notify_new_user_welcome(instance)

        notify_admins_new_user(instance)


