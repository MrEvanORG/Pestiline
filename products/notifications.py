import ghasedak_sms
from django.core.mail import send_mail
from django.conf import settings as django_settings
from .models import User, MessageSiteSettings, NotificationLog

sms_api = ghasedak_sms.Ghasedak(api_key=f'{django_settings.SMS_API}')
mss = MessageSiteSettings.objects.first()

def send_sms_mock(phone_number, text):
    if django_settings.DEV_MODE : 
        print(f"\n{'='*40}")
        print(f" MESSAGE SENT (SUCCESS)")
        print(f"To: {phone_number}")
        print(f"MESSAGE: {text}")
        print(f"{'='*40}\n")
    else:
        response = sms_api.send_single_sms(
            ghasedak_sms.SendSingleSmsInput(
                message=text,
                receptor=str(phone_number),
                line_number=str(mss.primary_line_number), # type: ignore
                send_date='',
                client_reference_id=''
            )
        )
        if not response.get('isSuccess'): # type: ignore
            raise Exception(response.get('message', 'خطای نامشخص')) # type: ignore
        
def send_email_mock(plain_message,email_context):
    html_message = render_to_string('products/emails/base_email.html', email_context)
    email = EmailMultiAlternatives(
        subject,
        plain_message,      # بدنه اصلی (متن ساده)
        None,               # از DEFAULT_FROM_EMAIL در settings استفاده کن
        recipient_list,
        reply_to=[reply_to] # بسیار مهم برای پاسخ مستقیم
    )
    email.attach_alternative(html_message, "text/html") # پیوست کردن نسخه HTML
    email.send()

def notify_new_user_welcome(user):
    settings = MessageSiteSettings.objects.first()
    
    # بررسی فعال بودن تنظیمات خوشامدگویی کاربر
    if not settings or settings.tu_wellcome != MessageSiteSettings.NotifStatusChoices.ENABLE or not user.phone_number:
        return

    message = f"{user.first_name} عزیز به پستیلاین خوش آمدید\nحساب شما با موفقیت ایجاد شد در صورت بروز هرگونه مشکل با پشتیبانی در ارتباط باشید .\nلغو 11"
    status = 'SUCCESS'
    error_details = None

    try:
        send_sms_mock(user.phone_number, message)
    except Exception as e:
        status = 'FAILED'
        error_details = str(e)[:220]

    # ثبت لاگ
    NotificationLog.objects.create(
        user=user,
        notification_type='SMS',
        related_event=NotificationLog.EventChoices.NEW_USER_TU,
        message_content=message,
        status=status,
        error_details=error_details
    )

def notify_admins_new_user(new_user):
    settings = MessageSiteSettings.objects.first()
    
    # بررسی فعال بودن تنظیمات اطلاع‌رسانی ثبت‌نام به ادمین
    if not settings or settings.ta_new_user != MessageSiteSettings.NotifStatusChoices.ENABLE:
        return

    message = f"کاربر {new_user.first_name+' '+new_user.last_name} در پستیلاین ثبت نام کرد\nلغو11"
    
    superusers = User.objects.filter(is_superuser=True)
    
    for admin in superusers:
        pref = admin.prefered_notification
        
        if pref == User.PrederefNotifChoices.DISABLE:
            continue
            
        status = 'SUCCESS'
        error_details = None
        notif_type = 'SMS'

        try:
            if pref == User.PrederefNotifChoices.MESSAGE:
                notif_type = 'SMS'
                send_sms_mock(admin.phone_number, message)
                
            elif pref == User.PrederefNotifChoices.EMAIL:
                notif_type = 'EMAIL'
                email_context = {
                    'subject': subject,
                    'main_title': 'ثبت نام کاربر جدید',
                    'content_title': f'کاربر {new_user.get_full_name()} روی سایت ثبت نام کرد ',
                    'name': name,
                    'reply_to': reply_to,
                    'user_message': user_message,
                    'cta_text': 'مشاهده سفارش در سایت',
                    'cta_link': request.build_absolute_uri(
                        reverse('resume_detail', kwargs={'slug': slug})
                    )
                }
                plain_message = f"نام فرستنده: {name}\nتماس: {reply_to}\n\nمتن پیام:\n{user_message}"
                send_email_mock(plain_message=plain_message,email_context=email_context)
                
                # send_mail(
                #     subject="ثبت نام کاربر جدید",
                #     message=message,
                #     from_email=None,
                #     recipient_list=[admin.email],
                #     fail_silently=False,
                # )
        except Exception as e:
            status = 'FAILED'
            error_details = str(e)[:220]

        NotificationLog.objects.create(
            user=admin,
            notification_type=notif_type,
            related_event=NotificationLog.EventChoices.NEW_USER_TA,
            message_content=message,
            status=status,
            error_details=error_details
        )

def notify_user_new_order(order):
    settings = MessageSiteSettings.objects.first()
    
    # بررسی فعال بودن تنظیمات اطلاع رسانی ثبت سفارش به مشتری
    if not settings or settings.tu_new_order != MessageSiteSettings.NotifStatusChoices.ENABLE:
        return

    customer = order.customer
    pref = customer.prefered_notification
    
    if pref == User.PrederefNotifChoices.DISABLE:
        return

    message = f"{order.customer.first_name} عزیز سفارش شما ثبت شد همکاران  ما جهت پرداخت هزینه با شما تماس خواهند گرفت\nهمچنین برای مشاهده وضعیت سفارش میتوانید از طریق پنل کاربری اقدام نمایید .\nلغو11"

    status = 'SUCCESS'
    error_details = None
    notif_type = 'SMS'

    try:
        if pref == User.PrederefNotifChoices.MESSAGE:
            notif_type = 'SMS'
            send_sms_mock(customer.phone_number, message)
            
        elif pref == User.PrederefNotifChoices.EMAIL:
            notif_type = 'EMAIL'
            send_mail(
                subject="ثبت سفارش جدید",
                message=message,
                from_email=None,
                recipient_list=[customer.email],
                fail_silently=False,
            )
    except Exception as e:
        status = 'FAILED'
        error_details = str(e)[:220]

    NotificationLog.objects.create(
        user=customer,
        notification_type=notif_type,
        related_event=NotificationLog.EventChoices.NEW_ORDER_TU,
        message_content=message,
        status=status,
        error_details=error_details
    )

def notify_admins_new_order(order):
    settings = MessageSiteSettings.objects.first()
    
    # بررسی فعال بودن اطلاع رسانی سفارش جدید به ادمین
    if not settings or settings.ta_new_order != MessageSiteSettings.NotifStatusChoices.ENABLE:
        return
    
    message = f"ادمین محترم کاربر {order.customer.get_full_name} سفارشی با شماره {order.order_number}  ثبت کرد و در انتظار پرداخت است.\nلغو11"

    superusers = User.objects.filter(is_superuser=True)
    
    for admin in superusers:
        pref = admin.prefered_notification
        
        if pref == User.PrederefNotifChoices.DISABLE:
            continue
            
        status = 'SUCCESS'
        error_details = None
        notif_type = 'SMS'

        try:
            if pref == User.PrederefNotifChoices.MESSAGE:
                notif_type = 'SMS'
                send_sms_mock(admin.phone_number, message)
                
            elif pref == User.PrederefNotifChoices.EMAIL:
                notif_type = 'EMAIL'
                send_mail(
                    subject="سفارش جدید",
                    message=message,
                    from_email=None,
                    recipient_list=[admin.email],
                    fail_silently=False,
                )
        except Exception as e:
            status = 'FAILED'
            error_details = str(e)[:220]

        NotificationLog.objects.create(
            user=admin,
            notification_type=notif_type,
            related_event=NotificationLog.EventChoices.NEW_ORDER_TA,
            message_content=message,
            status=status,
            error_details=error_details
        )
