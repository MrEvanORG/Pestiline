import os
from django.db.models.signals import post_delete, pre_save , post_save
from django.dispatch import receiver
from .models import ProductImage , Order , User
from .notifications import  new_user_notif , new_order_notif

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

@receiver(pre_save,sender=User)
def new_user_registered(sender , instance , **kwargs):
    if not instance.pk: #تشخیص ایجاد کاربر
        new_user_notif(instance)

@receiver(pre_save,sender=Order)
def new_order_submitted(sender , instance , **kwargs):

    if not instance.pk:
        return

    try:
        # دریافت وضعیت قبلی از دیتابیس
        old_order = Order.objects.get(pk=instance.pk)
        old_status = old_order.status
        new_status = instance.status

        # اگر وضعیت تغییر کرده است
        if old_status == 'CART' and new_status == 'PENDING':
            new_order_notif(instance)

    except Order.DoesNotExist:
        pass

