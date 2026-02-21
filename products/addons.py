import random
import logging
import time
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Province, City, SiteSettings

logger = logging.getLogger(__name__)

# ... (API های استان و شهر بدون تغییر) ...
@require_http_methods(["GET"])
def get_all_provinces(request):
    provinces = Province.objects.all().order_by('name')
    data = list(provinces.values('id', 'name'))
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def load_cities(request):
    province_id = request.GET.get('province_id')
    cities = City.objects.none()
    if province_id:
        cities = City.objects.filter(province_id=province_id).order_by('name')
    data = list(cities.values('id', 'name'))
    return JsonResponse(data, safe=False)

# ==========================================
# موتور ماژولار OTP
# ==========================================

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_otp_settings():
    try:
        settings = SiteSettings.objects.first()
        return settings.otp_time_interval if settings else 120
    except:
        return 120

def check_rate_limit(request, phone_number):
    ip = get_client_ip(request)
    now = time.time()
    
    ip_key = f"otp_limit_ip_{ip}"
    phone_key = f"otp_limit_phone_{phone_number}"
    
    ip_expiry = cache.get(ip_key)
    phone_expiry = cache.get(phone_key)
    
    ttl = 0
    if ip_expiry and ip_expiry > now:
        ttl = int(ip_expiry - now)
    
    if phone_expiry and phone_expiry > now:
        phone_ttl = int(phone_expiry - now)
        if phone_ttl > ttl:
            ttl = phone_ttl

    if ttl > 0:
        return False, ttl

    return True, 0

def get_remaining_otp_time(request, phone_number):
    is_allowed, ttl = check_rate_limit(request, phone_number)
    if not is_allowed:
        return ttl
    return 0

def set_rate_limit(request, phone_number):
    ip = get_client_ip(request)
    timeout = get_otp_settings()
    expiry_time = time.time() + timeout
    
    ip_key = f"otp_limit_ip_{ip}"
    phone_key = f"otp_limit_phone_{phone_number}"
    
    cache.set(ip_key, expiry_time, timeout=timeout)
    cache.set(phone_key, expiry_time, timeout=timeout)

def send_otp_simulation(phone_number):
    """
    شبیه‌سازی ارسال پیامک با احتمال خطا برای تست
    """
    otp_code = str(random.randint(100000, 999999))
    
    # فرض کنیم همیشه 200 است، مگر اینکه بخواهیم تست کنیم
    # برای تست می‌توانید status_code را دستی تغییر دهید
    status_code = 200
    
    if status_code == 200:
        print(f"\n{'='*40}")
        print(f"🚀 OTP SENT (SUCCESS)")
        print(f"📱 To: {phone_number}")
        print(f"🔑 Code: {otp_code}")
        print(f"{'='*40}\n")
    else:
        print(f"\n❌ OTP FAILED TO SEND (Simulated Error)")

    return otp_code, status_code

def initiate_otp_process(request, phone_number, intent, extra_data=None):
    """
    تابع ماژولار شروع پروسه OTP
    """
    # ۱. بررسی محدودیت (Rate Limit)
    is_allowed, ttl = check_rate_limit(request, phone_number)
    
    rate_limited_status = False
    if not is_allowed:
        rate_limited_status = True

    # ۲. تلاش برای ارسال کد
    otp_code, api_status = send_otp_simulation(phone_number)
    
    # ============================================================
    # تغییر جدید: اگر ارسال پیامک با خطا مواجه شد (مثلا پنل قطع بود)
    # ============================================================
    if api_status != 200:
        logger.error(f"SMS Provider Error: Status {api_status} for {phone_number}")
        return {
            'success': False,
            'rate_limited': False,
            'message': 'خطا در ارسال پیامک. لطفاً دقایقی دیگر تلاش کنید.',
            'ttl': 0
        }
    
    # ۳. اعمال محدودیت جدید (فقط اگر محدودیت قبلی نداشته)
    if not rate_limited_status:
        set_rate_limit(request, phone_number)

    # ۴. ذخیره در سشن
    otp_context = {
        'phone_number': phone_number,
        'intent': intent,
        'otp_code': otp_code,
        'expiry': timezone.now().timestamp() + 300, 
        'extra_data': extra_data or {}
    }
    request.session['otp_context'] = otp_context

    # نتیجه موفقیت‌آمیز
    return {
        'success': True, 
        'rate_limited': rate_limited_status,
        'api_status': api_status,
        'ttl': ttl if rate_limited_status else get_otp_settings()
    }

# ... (کدهای قبلی فایل addons.py)

def send_order_status_sms(user, order_id, new_status):
    """
    شبیه‌سازی ارسال پیامک اطلاع‌رسانی وضعیت سفارش
    """
    phone = user.phone_number
    message = ""

    if new_status == 'PROCESSING':
        message = (
            f"سلام {user.first_name} عزیز،\n"
            f"رسید واریز سفارش #{order_id} تایید شد.\n"
            "سفارش شما در حال پردازش و آماده‌سازی است.\n"
            "پستیلاین"
        )
    
    elif new_status == 'SHIPPED':
        message = (
            f"سلام {user.first_name} عزیز،\n"
            f"سفارش #{order_id} تحویل پست گردید.\n"
            "به زودی کد پیگیری برای شما ارسال خواهد شد.\n"
            "پستیلاین"
        )
    
    elif new_status == 'CANCELED':
        message = (
            f"کاربر گرامی،\n"
            f"سفارش #{order_id} لغو گردید.\n"
            "در صورت کسر وجه، مبلغ طی ۷۲ ساعت به حساب شما بازمی‌گردد.\n"
            "پستیلاین"
        )

    if message:
        print(f"\n{'='*40}")
        print(f"📨 SMS SIMULATION TO: {phone}")
        print(f"{'-'*20}")
        print(message)
        print(f"{'='*40}\n")