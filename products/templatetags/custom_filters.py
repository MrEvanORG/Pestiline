import jdatetime
from django import template
from django.utils import timezone
import datetime
register = template.Library()

@register.filter
def format_weight(value):
    try:
        kilos = int(value)
        grams = int(round((value - kilos) * 1000))
        result = ""

        if kilos > 0:
            result += f"{kilos} کیلوگرم"
        if grams > 0:
            result += f" و {grams} گرم" if kilos > 0 else f"{grams} گرم"
        if not result:
            result = "۰ گرم"

        return result
    except:
        return value

@register.filter
def to_jalali(value, form):
    if not value:
        return ""
    try:
        if isinstance(value, datetime.datetime):
            value = timezone.localtime(value)
        elif isinstance(value, datetime.date):
            value = datetime.datetime.combine(value, datetime.time.min)
        
        # ۲. تبدیل به شمسی
        jalali_datetime = jdatetime.datetime.fromgregorian(datetime=value)
        
        if form == "numeric_date":
            return jalali_datetime.strftime('%Y/%m/%d')
        elif form == "numeric_date_time":
            return jalali_datetime.strftime('%Y/%m/%d - %H:%M')
        elif form == "persian_date":
            # اضافه کردن لوکال فارسی برای نام روزها و ماه‌ها
            jalali_datetime = jdatetime.datetime.fromgregorian(datetime=value, locale=jdatetime.FA_LOCALE)
            return jalali_datetime.strftime('%A %d %B %Y')
        elif form == "persian_date_time":
            jalali_datetime = jdatetime.datetime.fromgregorian(datetime=value, locale=jdatetime.FA_LOCALE)
            return jalali_datetime.strftime('%A %d %B %Y - %H:%M')
    except Exception as e:
        return f"Error: {str(e)}" # برای دیباگ می‌توانید موقتا این را بگذارید
    return ""

@register.simple_tag
def get_jalali_admin_time():
    # گرفتن تاریخ فعلی سیستم
    now = timezone.now()

    jtime = jdatetime.datetime.fromgregorian(datetime=now,locale=jdatetime.FA_LOCALE)
    
    date_str = jtime.strftime("%A %d %B %Y")
    
    en_to_fa = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    return date_str.translate(en_to_fa)
    