
import ghasedak_sms
from django.contrib.auth import get_user_model
from django.conf import settings as django_settings
from .models import MessageSiteSettings , SiteSettings , User as UserType , Order

User = get_user_model()
message_setting = MessageSiteSettings.objects.first()
sms_api = ghasedak_sms.Ghasedak(api_key=django_settings.SMS_API)


def new_user_notif(user_instance:UserType):
    pass

    # if user_instance.phone_number:
    #     if message_setting.ta_new_user == MessageSiteSettings.NotifStatusChoices.ENABLE :

    #         message_admins = User.objects.filter(is_superuser=True,prefered_notification="MESSAGE")
    #         for admin in message_admins:
    #             print("sending message new user to ",admin.username)

    #         email_admins = User.objects.filter(is_superuser=True,prefered_notification="EMAIL")
    #         for admin in email_admins:
    #             print("sending email new user to",admin.username)


        # if message_setting.tu_wellcome == MessageSiteSettings.NotifStatusChoices.ENABLE: 
            # if user_instance.prefered_notification == UserType.PrederefNotifChoices.MESSAGE:
            #     print("sending wellcome message to user",user_instance.get_full_name())
            # elif user_instance.prefered_notification == UserType.PrederefNotifChoices.EMAIL:
            #     print("sending wellcome email to user",user_instance.get_full_name())


def new_order_notif(order_instance:Order):
    pass

    #ارسال اطلاع سفارش جدید به ادمین
    # if message_setting.ta_new_order == MessageSiteSettings.NotifStatusChoices.ENABLE :

        # message_admins = User.objects.filter(is_superuser=True,prefered_notification="MESSAGE")
        # for admin in message_admins:
        #     print("sending message new order to admin",admin.username)

        # email_admins = User.objects.filter(is_superuser=True,prefered_notification="EMAIL")
        # for admin in email_admins:
        #     print("sending email new order to admin",admin.username)

    #ارسال اطلاع سفارش جدید به کاربر
    # if message_setting.tu_new_order == MessageSiteSettings.NotifStatusChoices.ENABLE:
    #     if order_instance.customer.phone_number:
    #         #ارسال تکمیل سبد خرید و کد پیگیری سفارش 
    #         if order_instance.customer.prefered_notification == "MESSAGE":
    #             print("sending message new order to user",order_instance.customer.get_full_name())

    #         elif order_instance.customer.prefered_notification == "EMAIL":
    #             print("sending email new order to user",order_instance.customer.get_full_name())

