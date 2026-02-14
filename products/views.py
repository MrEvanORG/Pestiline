import json
import time
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from .forms import UserRegisterForm, UserLoginForm
from .models import User, Province, City
from .addons import initiate_otp_process, get_otp_settings, get_remaining_otp_time

# ... (صفحات عمومی بدون تغییر) ...
def index_page(request): return render(request, 'index.html')
@login_required(login_url='auth')
def dashboard_page(request): return HttpResponse(f"خوش آمدید {request.user.first_name}!")

# ==========================================
# سیستم احراز هویت ماژولار
# ==========================================
def auth_page(request):
    # اگر کاربر قبلاً لاگین کرده، نیازی به دیدن این صفحه ندارد
    if request.user.is_authenticated:
        return redirect('dashboard')

    login_form = UserLoginForm()
    register_form = UserRegisterForm()
    active_tab = 'login'
    
    selected_province_name = ''
    selected_city_name = ''

    # ============================================================
    # بخش GET: بازیابی اطلاعات (اگر کاربر از صفحه OTP برگردد)
    # ============================================================
    if request.method == 'GET' and 'otp_context' in request.session:
        context_data = request.session['otp_context']
        # فقط اگر هدف ثبت‌نام بوده، فرم را پر کن
        if context_data.get('intent') == 'register':
            extra = context_data.get('extra_data', {})
            initial_data = {
                'phone_number': context_data.get('phone_number'),
                **extra 
            }
            # مپ کردن ID ها به نام فیلدهای فرم
            if 'province_id' in extra: initial_data['province'] = extra['province_id']
            if 'city_id' in extra: initial_data['city'] = extra['city_id']

            register_form = UserRegisterForm(initial=initial_data)
            active_tab = 'register'
            
            # بازیابی نام شهر/استان برای UI
            try:
                if extra.get('province_id'): selected_province_name = Province.objects.get(pk=extra['province_id']).name
                if extra.get('city_id'): selected_city_name = City.objects.get(pk=extra['city_id']).name
            except: pass

    # ============================================================
    # بخش POST: پردازش فرم‌ها
    # ============================================================
    if request.method == 'POST':
        # --- سناریوی لاگین ---
        if 'login_submit' in request.POST:
            login_form = UserLoginForm(request.POST)
            if login_form.is_valid():
                phone = login_form.cleaned_data['phone_number']
                password = login_form.cleaned_data['password']
                user = authenticate(request, phone_number=phone, password=password)
                if user:
                    login(request, user)
                    return redirect('dashboard')
                else:
                    login_form.add_error(None, 'اطلاعات ورود اشتباه است.')
            active_tab = 'login'

        # --- سناریوی ثبت‌نام ---
        elif 'register_submit' in request.POST:
            register_form = UserRegisterForm(request.POST)
            if register_form.is_valid():
                # ۱. دریافت داده‌های فرم
                phone = register_form.cleaned_data['phone_number']
                extra_data = {
                    'first_name': register_form.cleaned_data['first_name'],
                    'last_name': register_form.cleaned_data['last_name'],
                    'province_id': register_form.cleaned_data['province'].id,
                    'city_id': register_form.cleaned_data['city'].id,
                    'password': register_form.cleaned_data.get('password'),
                    'otp_request': register_form.cleaned_data.get('otp_request')
                }

                # ۲. تصمیم‌گیری برای ارسال مجدد (جلوگیری از هدررفت هزینه پیامک)
                should_send_new_otp = True
                
                if 'otp_context' in request.session:
                    old_context = request.session['otp_context']
                    # اگر شماره تغییر نکرده و پروسه قبلی هم ثبت‌نام بوده
                    if old_context.get('phone_number') == phone and old_context.get('intent') == 'register':
                        # چک کردن تایمر فعال
                        ttl = get_remaining_otp_time(request, phone)
                        if ttl > 0:
                            should_send_new_otp = False
                            # فقط اطلاعات (مثل نام یا شهر اصلاح شده) را آپدیت می‌کنیم
                            request.session['otp_context']['extra_data'] = extra_data
                            request.session.modified = True

                # ۳. اجرای عملیات بر اساس تصمیم بالا
                if should_send_new_otp:
                    # تلاش برای ارسال پیامک جدید
                    result = initiate_otp_process(
                        request, 
                        phone_number=phone, 
                        intent='register', 
                        extra_data=extra_data
                    )
                    
                    # === بخش اصلاح شده برای نمایش خطا ===
                    if result['success']:
                        # موفقیت کامل -> برو به صفحه کد
                        return redirect('verify_otp_page')
                    
                    elif result.get('rate_limited'):
                        # محدودیت زمانی دارد اما خطا نیست -> برو به صفحه کد (تایمر را می‌بیند)
                        return redirect('verify_otp_page')
                    
                    else:
                        # خطای واقعی (مثلاً پنل پیامک 200 نداده) -> ریدارکت نکن!
                        # نمایش خطا در همین صفحه
                        register_form.add_error(None, result['message'])
                
                else:
                    # نیاز به ارسال جدید نبود (تایمر فعال است) -> مستقیم برو
                    return redirect('verify_otp_page')
            
            # اگر فرم نامعتبر بود یا خطای ارسال پیامک داشتیم، در تب ثبت‌نام بمان
            active_tab = 'register'
            
            # بازیابی نام استان/شهر برای جلوگیری از پریدن UI در صورت خطا
            if register_form['province'].value():
                try: selected_province_name = Province.objects.get(pk=register_form['province'].value()).name
                except: pass
            if register_form['city'].value():
                try: selected_city_name = City.objects.get(pk=register_form['city'].value()).name
                except: pass

    context = {
        'login_form': login_form,
        'register_form': register_form,
        'active_tab': active_tab,
        'selected_province_name': selected_province_name,
        'selected_city_name': selected_city_name,
    }
    return render(request, 'auth.html', context)


# ... (بقیه توابع: verify_otp_page, verify_otp_api, resend_otp_api بدون تغییر) ...
# حتماً کدهای قبلی verify_otp_page و APIها را در ادامه فایل حفظ کنید
def verify_otp_page(request):
    if 'otp_context' not in request.session:
        return redirect('auth')
    context_data = request.session['otp_context']
    phone = context_data.get('phone_number')
    remaining_time = get_remaining_otp_time(request, phone)
    timer_duration = remaining_time if remaining_time > 0 else 0
    return render(request, 'auth_verify_otp.html', {
        'user_phone': phone,
        'timer_duration': timer_duration
    })

@require_POST
def verify_otp_api(request):
    try:
        data = json.loads(request.body)
        user_code = str(data.get('code')).strip()
    except:
        return JsonResponse({'success': False, 'message': 'فرمت نامعتبر'}, status=400)

    otp_context = request.session.get('otp_context')
    if not otp_context:
        return JsonResponse({'success': False, 'message': 'نشست منقضی شده.'}, status=400)

    session_code = str(otp_context.get('otp_code', '')).strip()
    expiry = otp_context.get('expiry')
    intent = otp_context.get('intent')
    
    if time.time() > expiry:
        return JsonResponse({'success': False, 'message': 'کد منقضی شده است.'}, status=400)

    if user_code == session_code:
        if intent == 'register':
            extra = otp_context.get('extra_data', {})
            try:
                from .models import User, Province, City 
                province = Province.objects.get(id=extra['province_id'])
                city = City.objects.get(id=extra['city_id'])
                phone = otp_context['phone_number']
                user = User(
                    first_name=extra['first_name'],
                    last_name=extra['last_name'],
                    phone_number=phone,
                    username=phone,
                    province=province,
                    city=city
                )
                if extra.get('password'): user.set_password(extra['password'])
                else: user.set_unusable_password()
                user.save()
                login(request, user)
                del request.session['otp_context']
                return JsonResponse({'success': True, 'redirect_url': reverse('dashboard')})
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'خطای ثبت‌ نام: {str(e)}'}, status=500)
        elif intent == 'login':
            # لاگین پیاده سازی شود
            return JsonResponse({'success': True, 'redirect_url': reverse('dashboard')})
        elif intent == 'reset_password':
             return JsonResponse({'success': True, 'redirect_url': '/auth/reset-password-confirm/'})
    else:
        return JsonResponse({'success': False, 'message': 'کد نادرست است.'}, status=400)

@require_POST
def resend_otp_api(request):
    otp_context = request.session.get('otp_context')
    if not otp_context:
        return JsonResponse({'success': False, 'message': 'نشست نامعتبر'}, status=403)
    phone = otp_context.get('phone_number')
    intent = otp_context.get('intent')
    extra = otp_context.get('extra_data')
    result = initiate_otp_process(request, phone, intent, extra)
    if result['success'] and not result['rate_limited']:
        return JsonResponse({'success': True, 'message': 'کد جدید ارسال شد.', 'ttl': result['ttl']})
    else:
        if result['rate_limited']:
             return JsonResponse({'success': False, 'message': 'لطفاً صبر کنید.', 'ttl': result['ttl']}, status=429)
        return JsonResponse({'success': False, 'message': 'خطا در ارسال.'}, status=500)