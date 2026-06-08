import ghasedak_sms
from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import User, MessageSiteSettings, NotificationLog

sms_api = ghasedak_sms.Ghasedak(api_key=f'{django_settings.SMS_API}')

BASE_URL = "https://pestiline.ir" 

def get_mss():
    return MessageSiteSettings.objects.first()

def get_admin_url(instance):
    """
    تولید آدرس پویای پنل ادمین بر اساس متغیر امنیتی ADMIN_URL در ستینگز
    """
    admin_prefix = getattr(django_settings, 'ADMIN_URL', 'admin').strip('/')
    app_label = instance._meta.app_label
    model_name = instance._meta.model_name
    return f"{BASE_URL}/{admin_prefix}/{app_label}/{model_name}/{instance.id}/change/"

def send_sms_mock(phone_number, text):
    mss = get_mss()
    if getattr(django_settings, 'DEV_MODE', False): 
        print(f"\n{'='*40}\n MESSAGE SENT (SUCCESS)\nTo: {phone_number}\nMESSAGE:\n{text}\n{'='*40}\n")
    else:
        response = sms_api.send_single_sms(
            ghasedak_sms.SendSingleSmsInput(
                message=text,
                receptor=str(phone_number),
                line_number=str(mss.primary_line_number) if mss and mss.primary_line_number else '', 
                send_date='',
                client_reference_id=''
            )
        )
        if not response.get('isSuccess'):
            raise Exception(response.get('message', 'خطای نامشخص در ارسال پیامک'))

def send_email_mock(subject, plain_message, email_context, recipient_email):
    html_message = render_to_string('products/emails/base_email.html', email_context)
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,      
        from_email=django_settings.DEFAULT_FROM_EMAIL,               
        to=[recipient_email],
    )
    email.attach_alternative(html_message, "text/html") 
    email.send()

def dispatch_notification(user, event_type, sms_msg, email_subj, email_plain, email_context):
    """ هسته مرکزی پردازش، اعتبارسنجی و لاگ‌گیری """
    pref = user.prefered_notification
    if pref == User.PrederefNotifChoices.DISABLE: return

    status, error_details, notif_type = 'SUCCESS', None, pref

    try:
        if pref == User.PrederefNotifChoices.MESSAGE:
            notif_type = 'SMS'
            if not user.phone_number: raise Exception("شماره موبایل ثبت نشده است.")
            send_sms_mock(user.phone_number, sms_msg)
            
        elif pref == User.PrederefNotifChoices.EMAIL:
            notif_type = 'EMAIL'
            if not user.email: raise Exception("ایمیل کاربر ثبت نشده است.")
            send_email_mock(email_subj, email_plain, email_context, user.email)
            
    except Exception as e:
        status, error_details = 'FAILED', str(e)[:220]

    NotificationLog.objects.create(
        user=user, notification_type=notif_type, related_event=event_type,
        message_content=sms_msg if notif_type == 'SMS' else email_plain,
        status=status, error_details=error_details
    )

# ================== TO USER (TU) ==================

def notify_new_user_welcome(user):
    mss = get_mss()
    if not mss or mss.tu_wellcome != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    first_name = user.first_name if user.first_name else "کاربر"
    sms_msg = f"{first_name} عزیز، به پستیلاین خوش آمدید.\nحساب کاربری شما با موفقیت ایجاد شد.\nلغو 11"
    
    email_context = {
        'subject': 'ثبت نام موفق در پستیلاین', 
        'main_title': 'خوش‌آمدید',
        'top_greeting': f'کاربر گرامی {first_name}،',
        'top_message': 'ثبت نام شما با موفقیت انجام شد. از اینکه به پستیلاین پیوستید خرسندیم. هم‌اکنون می‌توانید از خدمات سایت استفاده نمایید.',
        'info_box_title': 'اطلاعات حساب کاربری',
        'info_items': [
            {'label': 'نام', 'value': user.get_full_name() or 'ثبت نشده'},
            {'label': 'شماره همراه', 'value': user.phone_number},
        ],
        'cta_text': 'ورود به حساب کاربری', 
        'cta_link': f"{BASE_URL}",
    }
    dispatch_notification(user, NotificationLog.EventChoices.NEW_USER_TU, sms_msg, email_context['subject'], "ثبت نام شما با موفقیت در پستیلاین انجام شد.", email_context)

def notify_user_submit_order(order):
    mss = get_mss()
    if not mss or mss.tu_submit_order != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    user = order.customer
    first_name = user.first_name if user.first_name else "کاربر"
    sms_msg = f"{first_name} عزیز، سفارش شما با شماره {order.order_number} ثبت شد و در انتظار بررسی است.\nلغو 11"
    
    email_context = {
        'subject': f'سفارش شماره {order.order_number} با موفقیت ثبت شد', 
        'main_title': 'ثبت موفق سفارش',
        'top_greeting': f'کاربر گرامی {first_name}،', 
        'top_message': 'سفارش شما با موفقیت در سیستم ثبت گردید و در مرحله بررسی توسط کارشناسان قرار گرفت. وضعیت سفارش از طریق پنل کاربری قابل پیگیری است.',
        'info_box_title': 'جزئیات کامل سفارش',
        'info_items': [
            {'label': 'شماره سفارش', 'value': order.order_number},
            {'label': 'مبلغ کل پرداخت', 'value': f"{order.total_price:,} تومان"},
            {'label': 'گیرنده', 'value': order.receiver_name},
            {'label': 'آدرس ارسال', 'value': order.address},
        ],
        'cta_text': 'پیگیری وضعیت سفارش', 
        'cta_link': f"{BASE_URL}",
    }
    dispatch_notification(user, NotificationLog.EventChoices.NEW_ORDER_TU, sms_msg, email_context['subject'], f"سفارش {order.order_number} ثبت گردید.", email_context)

def notify_user_send_order(order):
    mss = get_mss()
    if not mss or mss.tu_send_order != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    user = order.customer
    first_name = user.first_name if user.first_name else "کاربر"
    
    sms_msg = f"{first_name} عزیز، سفارش شما با شماره {order.order_number} ارسال شد."
    info_items = [
        {'label': 'شماره سفارش', 'value': order.order_number},
        {'label': 'گیرنده', 'value': order.receiver_name},
    ]
    
    if order.tracking_code:
        sms_msg += f"\nکد رهگیری: {order.tracking_code}"
        info_items.extend([
            {'label': 'کد رهگیری پستی', 'value': order.tracking_code},
            {'label': 'سامانه پیگیری', 'value': 'tracking.post.ir', 'is_link': True}
        ])
    sms_msg += "\nلغو 11"

    email_context = {
        'subject': f'سفارش شماره {order.order_number} ارسال شد', 
        'main_title': 'وضعیت: ارسال شده',
        'top_greeting': f'کاربر گرامی {first_name}،', 
        'top_message': 'سفارش شما بسته بندی و به اداره پست تحویل داده شد. در صورت وجود کد رهگیری، می‌توانید مرسوله خود را در سامانه پست پیگیری نمایید.',
        'info_box_title': 'اطلاعات ارسال مرسوله', 
        'info_items': info_items,
        'cta_text': 'مشاهده تاریخچه سفارشات', 
        'cta_link': f"{BASE_URL}",
    }
    dispatch_notification(user, NotificationLog.EventChoices.SENT_ORDER_TU, sms_msg, email_context['subject'], f"سفارش {order.order_number} ارسال گردید.", email_context)

def notify_user_new_ticket(ticket):
    mss = get_mss()
    if not mss or mss.tu_new_ticket != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    user = ticket.user
    first_name = user.first_name if user.first_name else "کاربر"
    sms_msg = f"{first_name} عزیز، تیکت شما با شماره {ticket.ticket_number} در سیستم ثبت شد و در اسرع وقت بررسی می‌گردد.\nلغو 11"
    
    email_context = {
        'subject': f'تیکت پشتیبانی شماره {ticket.ticket_number} ثبت شد', 
        'main_title': 'تیکت دریافت شد',
        'top_greeting': f'کاربر گرامی {first_name}،', 
        'top_message': 'تیکت شما با موفقیت در سیستم ثبت شد. کارشناسان ما در حال بررسی موضوع می‌باشند و به زودی پاسخگو خواهند بود.',
        'info_box_title': 'اطلاعات تیکت',
        'info_items': [
            {'label': 'شماره پیگیری', 'value': ticket.ticket_number},
            {'label': 'موضوع گفتگو', 'value': ticket.get_subject_type_display()},
        ],
        'cta_text': 'مشاهده تیکت در سایت', 
        'cta_link': f"{BASE_URL}",
    }
    dispatch_notification(user, NotificationLog.EventChoices.NEW_TICKET_TU, sms_msg, email_context['subject'], f"تیکت پشتیبانی {ticket.ticket_number} ثبت شد.", email_context)

def notify_user_ticket_message(ticket_message):
    mss = get_mss()
    if not mss or mss.tu_new_ticketmessage != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    ticket = ticket_message.ticket
    user = ticket.user
    first_name = user.first_name if user.first_name else "کاربر"
    sms_msg = f"{first_name} عزیز، پاسخ جدیدی از سوی پشتیبانی برای تیکت شماره {ticket.ticket_number} ثبت گردید.\nلغو 11"
    
    email_context = {
        'subject': f'پاسخ پشتیبانی به تیکت شماره {ticket.ticket_number}', 
        'main_title': 'پاسخ جدید دریافت شد',
        'top_greeting': f'کاربر گرامی {first_name}،',
        'top_message': 'کارشناسان پشتیبانی پاسخ جدیدی را برای گفتگوی شما ارسال کرده‌اند. متن پیام در ادامه قابل مشاهده است.',
        'user_message': ticket_message.text,
        'cta_text': 'ارسال پاسخ جدید', 
        'cta_link': f"{BASE_URL}",
    }
    dispatch_notification(user, NotificationLog.EventChoices.MSG_TICKET_TU, sms_msg, email_context['subject'], f"پاسخ پشتیبانی به تیکت {ticket.ticket_number} ثبت گردید.", email_context)

# ================== TO ADMIN (TA) ==================

def notify_admins_new_user(new_user):
    mss = get_mss()
    if not mss or mss.ta_new_user != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    sms_msg = f"اطلاع رسانی سیستم:\nکاربر جدید با شماره {new_user.phone_number} در سایت ثبت نام کرد.\nلغو 11"
    
    email_context = {
        'subject': 'ثبت نام کاربر جدید در سامانه', 
        'main_title': 'ثبت نام کاربر جدید',
        'top_greeting': 'مدیر محترم،',
        'top_message': 'یک کاربر جدید به تازگی در سامانه پستیلاین ثبت نام کرده است.',
        'info_box_title': 'اطلاعات کاربر',
        'info_items': [
            {'label': 'نام و نام خانوادگی', 'value': new_user.get_full_name() or 'ثبت نشده'},
            {'label': 'شماره همراه', 'value': new_user.phone_number},
        ],
        'cta_text': 'بررسی کاربر در پنل ادمین',
        'cta_link': get_admin_url(new_user),
    }
    for admin in User.objects.filter(is_superuser=True):
        dispatch_notification(admin, NotificationLog.EventChoices.NEW_USER_TA, sms_msg, email_context['subject'], f"ثبت نام جدید: {new_user.phone_number}", email_context)

def notify_admins_new_order(order):
    mss = get_mss()
    if not mss or mss.ta_new_order != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    sms_msg = f"اطلاع رسانی سیستم:\nسفارش جدید {order.order_number} توسط {order.customer.get_full_name()} ثبت شد.\nمبلغ: {order.total_price:,} تومان.\nلغو 11"
    
    email_context = {
        'subject': f'ثبت سفارش جدید شماره {order.order_number}', 
        'main_title': 'سفارش جدید',
        'top_greeting': 'مدیر محترم،',
        'top_message': 'یک سفارش جدید توسط مشتری در سایت ثبت شده و در انتظار بررسی و تایید شما قرار دارد.',
        'info_box_title': 'جزئیات سفارش',
        'info_items': [
            {'label': 'شماره سفارش', 'value': order.order_number},
            {'label': 'مشتری', 'value': order.customer.get_full_name()},
            {'label': 'مبلغ کل سفارش', 'value': f"{order.total_price:,} تومان"},
            {'label': 'هزینه ارسال', 'value': f"{order.shipping_cost:,} تومان" if order.shipping_cost else "نامشخص"},
        ],
        'cta_text': 'بررسی سفارش در پنل ادمین',
        'cta_link': get_admin_url(order),
    }
    for admin in User.objects.filter(is_superuser=True):
        dispatch_notification(admin, NotificationLog.EventChoices.NEW_ORDER_TA, sms_msg, email_context['subject'], f"سفارش جدید {order.order_number} ثبت گردید.", email_context)

def notify_admins_cancel_order(order):
    mss = get_mss()
    if not mss or mss.ta_cancell_order != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    sms_msg = f"هشدار سیستم:\nسفارش {order.order_number} متعلق به {order.customer.get_full_name()} پیش از پرداخت لغو گردید.\nلغو 11"
    
    email_context = {
        'subject': f'لغو سفارش شماره {order.order_number}', 
        'main_title': 'لغو سفارش',
        'top_greeting': 'مدیر محترم،',
        'top_message': 'کاربر پس از تایید سبد خرید و پیش از تکمیل فرآیند پرداخت، سفارش خود را لغو نموده است.',
        'info_box_title': 'اطلاعات سفارش لغو شده',
        'info_items': [
            {'label': 'شماره سفارش', 'value': order.order_number},
            {'label': 'مشتری', 'value': order.customer.get_full_name()},
            {'label': 'شماره همراه', 'value': order.customer.phone_number},
        ],
        'cta_text': 'مشاهده وضعیت سفارش در ادمین',
        'cta_link': get_admin_url(order),
    }
    for admin in User.objects.filter(is_superuser=True):
        dispatch_notification(admin, NotificationLog.EventChoices.CANCELL_ORDER_TA, sms_msg, email_context['subject'], f"سفارش {order.order_number} لغو گردید.", email_context)

def notify_admins_new_ticket(ticket):
    mss = get_mss()
    if not mss or mss.ta_new_ticket != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    sms_msg = f"اطلاع رسانی سیستم:\nتیکت جدید شماره {ticket.ticket_number} توسط {ticket.user.get_full_name()} در سایت ایجاد شد.\nلغو 11"
    
    email_context = {
        'subject': f'تیکت جدید شماره {ticket.ticket_number}', 
        'main_title': 'تیکت پشتیبانی جدید',
        'top_greeting': 'مدیر محترم،',
        'top_message': 'یک تیکت پشتیبانی جدید توسط کاربر ایجاد شده است و نیازمند بررسی کارشناسان می‌باشد.',
        'info_box_title': 'اطلاعات تیکت',
        'info_items': [
            {'label': 'شماره پیگیری', 'value': ticket.ticket_number},
            {'label': 'موضوع', 'value': ticket.get_subject_type_display()},
            {'label': 'ارسال کننده', 'value': ticket.user.get_full_name()},
        ],
        'cta_text': 'پاسخ به تیکت در پنل ادمین',
        'cta_link': get_admin_url(ticket),
    }
    for admin in User.objects.filter(is_superuser=True):
        dispatch_notification(admin, NotificationLog.EventChoices.NEW_TICKET_TA, sms_msg, email_context['subject'], f"تیکت جدید {ticket.ticket_number} ثبت شد.", email_context)

def notify_admins_ticket_message(ticket_message):
    mss = get_mss()
    if not mss or mss.ta_new_ticketmessage != MessageSiteSettings.NotifStatusChoices.ENABLE: return
    
    ticket = ticket_message.ticket
    sms_msg = f"اطلاع رسانی سیستم:\nپاسخ جدیدی توسط کاربر در تیکت شماره {ticket.ticket_number} ثبت گردید.\nلغو 11"
    
    email_context = {
        'subject': f'پیام جدید در تیکت شماره {ticket.ticket_number}', 
        'main_title': 'پیام جدید کاربر',
        'top_greeting': 'مدیر محترم،',
        'top_message': 'کاربر پاسخ جدیدی را بر روی تیکت قبلی خود ارسال نموده است.',
        'info_box_title': 'اطلاعات تیکت',
        'info_items': [
            {'label': 'شماره پیگیری', 'value': ticket.ticket_number},
            {'label': 'ارسال کننده', 'value': ticket.user.get_full_name()},
        ],
        'user_message': ticket_message.text,
        'cta_text': 'بررسی تیکت در پنل ادمین',
        'cta_link': get_admin_url(ticket),
    }
    for admin in User.objects.filter(is_superuser=True):
        dispatch_notification(admin, NotificationLog.EventChoices.MSG_TICKET_TA, sms_msg, email_context['subject'], f"پیام جدید در تیکت {ticket.ticket_number} ثبت گردید.", email_context)