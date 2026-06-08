import os
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from .models import ProductImage, Order, User, Ticket, TicketMessage, SiteSettings

# ---------------------------------------------------------
# سیگنال‌های محصولات، تیکت‌ها و تنظیمات (دست‌نخورده از قبل)
# ---------------------------------------------------------
@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path): os.remove(instance.image.path)

@receiver(pre_save, sender=ProductImage)
def delete_old_image_on_update(sender, instance, **kwargs):
    if not instance.pk: return False
    try: old_file = sender.objects.get(pk=instance.pk).image
    except sender.DoesNotExist: return False
    new_file = instance.image
    if not old_file == new_file and os.path.isfile(old_file.path): os.remove(old_file.path)

@receiver(post_delete, sender=TicketMessage)
def delete_ticket_message_attachment(sender, instance, **kwargs):
    if instance.attachment and os.path.isfile(instance.attachment.path): os.remove(instance.attachment.path)

@receiver(pre_save, sender=TicketMessage)
def delete_old_attachment_on_update(sender, instance, **kwargs):
    if not instance.pk: return False
    try: old_file = sender.objects.get(pk=instance.pk).attachment
    except sender.DoesNotExist: return False
    new_file = instance.attachment
    if old_file and old_file != new_file and os.path.isfile(old_file.path): os.remove(old_file.path)

@receiver(post_delete, sender=SiteSettings)
def delete_welcome_song_on_delete(sender, instance, **kwargs):
    if instance.welcome_song: instance.welcome_song.delete(save=False)

@receiver(pre_save, sender=SiteSettings)
def delete_old_welcome_song_on_update(sender, instance, **kwargs):
    if not instance.pk: return
    try: old_instance = SiteSettings.objects.get(pk=instance.pk)
    except SiteSettings.DoesNotExist: return
    if old_instance.welcome_song and old_instance.welcome_song != instance.welcome_song:
        old_instance.welcome_song.delete(save=False)


# ---------------------------------------------------------
# سیگنال‌های اطلاع‌رسانی پستیلاین (منطق تجاری جدید)
# ---------------------------------------------------------

@receiver(post_save, sender=User)
def handle_new_user_registration(sender, instance, created, **kwargs):
    from .notifications import notify_new_user_welcome, notify_admins_new_user
    if created:
        notify_new_user_welcome(instance)
        notify_admins_new_user(instance)

# --- منطق تغییر وضعیت سفارش ---
@receiver(pre_save, sender=Order)
def capture_old_order_state(sender, instance, **kwargs):
    """ ذخیره وضعیت قبلی سفارش برای مقایسه در post_save """
    if instance.pk:
        try:
            instance._old_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Order)
def handle_order_status_changes(sender, instance, created, **kwargs):
    from .notifications import notify_user_submit_order, notify_admins_new_order, notify_user_send_order, notify_admins_cancel_order
    
    old_status = getattr(instance, '_old_status', None)

    # حالت اول: کاربر سفارش را نهایی کرده و در انتظار پرداخت است
    if old_status == 'CART' and instance.status == 'PENDING':
        notify_user_submit_order(instance)
        notify_admins_new_order(instance)

    # حالت دوم: کاربر پشیمان شده و سفارش پرداخت نشده را لغو کرده (برگشت به سبد خرید)
    elif old_status == 'PENDING' and instance.status == 'CART':
        notify_admins_cancel_order(instance)

    # حالت سوم: ادمین وضعیت سفارش را به ارسال شده تغییر داده است
    elif old_status != 'SHIPPED' and instance.status == 'SHIPPED':
        notify_user_send_order(instance)

@receiver(post_delete, sender=Order)
def handle_order_deletion(sender, instance, **kwargs):
    """ اگر کاربر به جای لغو، کل آبجکت سفارش را حذف کرد، به ادمین هشدار لغو برود """
    from .notifications import notify_admins_cancel_order
    if instance.status == 'PENDING':
        notify_admins_cancel_order(instance)

# --- منطق تیکت‌ها ---
@receiver(post_save, sender=Ticket)
def handle_new_ticket_creation(sender, instance, created, **kwargs):
    from .notifications import notify_admins_new_ticket, notify_user_new_ticket
    if created:
        notify_admins_new_ticket(instance)
        notify_user_new_ticket(instance)

@receiver(post_save, sender=TicketMessage)
def handle_new_ticket_message(sender, instance, created, **kwargs):
    from .notifications import notify_admins_ticket_message, notify_user_ticket_message
    if created:
        # اگر فرستنده ادمین بود -> به کاربر پیام بده
        if instance.is_admin_reply():
            notify_user_ticket_message(instance)
        # اگر فرستنده کاربر بود -> به ادمین‌ها پیام بده
        else:
            notify_admins_ticket_message(instance)