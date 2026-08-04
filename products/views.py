import json
import time
from decimal import Decimal
from django.urls import reverse 
from django.contrib import messages
from django.db.models import Count, Q , F
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import User, Province, City, Product, Order, OrderItem
from .forms import UserRegisterForm, UserLoginForm ,SetNewPasswordForm
from .addons import initiate_otp_process, get_otp_settings, get_remaining_otp_time , get_client_fingerprint
from blog.models import BlogPost
from django.core.cache import cache
from products.models import SiteSettings 
#-----------------------------------------------------------------------------------
def index_page(request): 
    # وضعیت‌های معتبر برای محاسبه یک فروش موفق
    valid_statuses = ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED']
    
    #گرفتن 4 تا از پرفروش ها و پر بازدیدترین ها
    featured_products = Product.objects.filter(active_status=True).annotate(
        total_sales=Count('orderitem', filter=Q(orderitem__order__status__in=valid_statuses))
    ).order_by('-visit_count', '-total_sales')[:4]

    blogposts = BlogPost.objects.filter(is_published=True)\
            .select_related('category', 'author')\
            .order_by('-created_at')[:3]
    
    context = {
        'posts':blogposts,
        'featured_products': featured_products
    }
    return render(request, 'index.html', context)




def get_cart_count(request):
    """محاسبه تعداد اقلام در سبد خرید فعال (وضعیت CART)"""
    if request.user.is_authenticated:
        #اگز کاربر ثبت نام شده باشه تعداد ایتم های سفارشش رو میگیریم
        order = Order.objects.filter(customer=request.user, status='CART').first()
        return order.items.count() if order else 0
    else:
        # اگر ریجستر شده نباشه از سشنش استفاده میکنیم
        cart = request.session.get('cart', {})
        return len(cart)

def merge_session_cart(request, user, explicit_cart=None):
    """
    ادغام سبد خرید.
    آرگومان explicit_cart برای زمانی است که سشن پس از لاگین تغییر کرده
    و می‌خواهیم نسخه قبل از لاگین را پاس بدهیم.
    """
    # اگر کارت صریح داده شد از آن استفاده کن، وگرنه از سشن فعلی بگیر
    session_cart = explicit_cart if explicit_cart is not None else request.session.get('cart', {})
    
    if not session_cart:
        return

    # ایجاد یا دریافت سفارش با وضعیت CART
    order, created = Order.objects.get_or_create(customer=user, status='CART')
    
    for product_id, item_data in session_cart.items():
        try:
            product = Product.objects.get(id=product_id)
            order_item, created = OrderItem.objects.get_or_create(
                order=order,
                product=product,
                defaults={
                    'quantity': item_data['quantity'],
                    'price': product.price
                }
            )
            if not created:
                order_item.quantity = item_data['quantity']
                order_item.save()
        except Product.DoesNotExist:
            continue
            
    order.calculate_total()
    
    # پاک کردن سبد از سشن جاری (چه جدید چه قدیم)
    request.session['cart'] = {}
    request.session.modified = True

@require_POST
def update_cart_api(request):
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        action = data.get('action')
        quantity = float(data.get('quantity', 1))
    except:
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    in_cart = False
    item_total = 0
    total_price = 0
    all_free_shipping = False

    # گرفتن محصول و محدود کردن مقدار مجاز (امنیت بک‌اند)
    if action in ['add', 'update']:
        product = get_object_or_404(Product, id=product_id)
        
        min_qty = product.min_order if product.min_order else (1.0 if product.sale_method == 'PACKAGED' else 0.1)
        max_qty = product.max_order if product.max_order else 1000.0
        
        if quantity < min_qty:
            quantity = min_qty
        elif quantity > max_qty:
            quantity = max_qty

    if request.user.is_authenticated:
        order, _ = Order.objects.get_or_create(customer=request.user, status='CART')
        
        if action == 'remove':
            OrderItem.objects.filter(order=order, product_id=product_id).delete()
            in_cart = False
        else: 
            item, created = OrderItem.objects.get_or_create(
                order=order, 
                product=product,
                defaults={'quantity': quantity, 'price': product.price}
            )
            
            # جلوگیری از تقلب: همیشه هنگام آپدیت، قیمت را با دیتابیس هماهنگ کن
            if not created or action == 'update':
                item.quantity = quantity
                item.price = product.price 
                item.save()
            
            in_cart = True
            item_total = item.quantity * item.price
        
        order.calculate_total()
        cart_count = order.items.count()
        # محاسبه جمع کل برای فرانت
        total_price = sum(i.quantity * i.price for i in order.items.all())
        if cart_count > 0:
            all_free_shipping = all(i.product.is_free_shipping for i in order.items.all())

    else:
        cart = request.session.get('cart', {})
        
        if action == 'remove':
            if product_id in cart:
                del cart[product_id]
            in_cart = False
        else: 
            # آپدیت سشن با مقدار محدود شده و قیمت واقعی
            cart[product_id] = {
                'quantity': quantity,
                'price': float(product.price)
            }
            in_cart = True
            item_total = quantity * float(product.price)
        
        request.session['cart'] = cart
        request.session.modified = True
        cart_count = len(cart)
        total_price = sum(v['quantity'] * v.get('price', 0) for v in cart.values())

    return JsonResponse({
        'success': True,
        'in_cart': in_cart,
        'cart_count': cart_count,
        'item_total': item_total,      # برای آپدیت قیمت همان ردیف
        'total_price': total_price,    # برای آپدیت پیش فاکتور
        'all_free_shipping': all_free_shipping,
        'message': 'سبد خرید بروز شد'
    })

# ==========================================
# سیستم احراز هویت ماژولار
# ==========================================
def auth_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
# ============================================================
    # سیستم هوشمند تشخیص مسیر ارجاع (Next URL) و تولید پیام مناسب
    # ============================================================
    next_url = request.GET.get('next')
    if next_url:
        request.session['next_url'] = next_url
        
        # پاک کردن پیام‌های قبلی برای جلوگیری از تکرار
        system_messages = messages.get_messages(request)
        for msg in system_messages: pass 
        
        # تولید پیام اختصاصی بر اساس مسیر
        if 'checkout' in next_url:
            messages.info(request, "برای نهایی کردن سفارش، لطفاً وارد حساب خود شوید یا ثبت‌نام کنید.")
        elif 'dashboard' in next_url:
            messages.info(request, "برای دسترسی به پنل کاربری، ابتدا باید وارد حساب خود شوید.")
        elif 'support' in next_url: # مثال برای مسیرهای آینده
            messages.info(request, "برای ثبت تیکت پشتیبانی، لطفاً وارد حساب کاربری خود شوید.")
        else:
            # پیام پیش‌فرض
            messages.info(request, "برای دسترسی به این بخش، لطفاً وارد حساب کاربری خود شوید.")

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
                    merge_session_cart(request, user)
                    next_url = request.session.pop('next_url', reverse('dashboard'))
                    return redirect(next_url)
                else:
                    login_form.add_error(None, 'اطلاعات ورود اشتباه است.')
            active_tab = 'login'

        # --- سناریوی ثبت‌نام ---
        elif 'register_submit' in request.POST:
            register_form = UserRegisterForm(request.POST)
            if register_form.is_valid():
                phone = register_form.cleaned_data['phone_number']
                extra_data = {
                    'first_name': register_form.cleaned_data['first_name'],
                    'last_name': register_form.cleaned_data['last_name'],
                    'province_id': register_form.cleaned_data['province'].id,
                    'city_id': register_form.cleaned_data['city'].id,
                    'password': register_form.cleaned_data.get('password'),
                    'otp_request': register_form.cleaned_data.get('otp_request')
                }

                # =========================================================================
                # راه حل قطعی: همیشه تابع اصلی را فراخوانی کنید.
                # این تابع خودش به درستی و با اطمینان، محدودیت زمانی را مدیریت می‌کند.
                # تمام منطق معیوب 'should_send_new_otp' حذف شده است.
                # =========================================================================
                result = initiate_otp_process(
                    request, 
                    phone_number=phone, 
                    intent='register', 
                    extra_data=extra_data
                )
                
                # بر اساس خروجی تابع امن، تصمیم بگیرید
                if result['success']:
                    # اگر کاربر در محدودیت زمانی بود اما اطلاعات فرم را تغییر داده بود، اطلاعات جدید را در سشن آپدیت کن
                    if result.get('rate_limited') and 'otp_context' in request.session:
                        request.session['otp_context']['extra_data'] = extra_data
                        request.session.modified = True
                        
                    return redirect('verify_otp_page')
                else:
                    # این حالت فقط زمانی رخ می‌دهد که یک خطای سیستمی در ارسال پیامک وجود داشته باشد.
                    register_form.add_error(None, result.get('message', 'خطای ناشناخته در ارسال کد.'))

            # اگر فرم نامعتبر بود یا خطایی رخ داد، در همان تب بمان
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
    """API بررسی کد یکبار مصرف (برای ثبت‌نام، ورود و بازیابی رمز)"""
    try:
        data = json.loads(request.body)
        user_code = str(data.get('code')).strip()
    except:
        return JsonResponse({'success': False, 'message': 'فرمت نامعتبر'}, status=400)

    # دریافت کانتکست
    otp_context = request.session.get('otp_context')
    if not otp_context:
        return JsonResponse({'success': False, 'message': 'نشست منقضی شده.'}, status=400)

    session_code = str(otp_context.get('otp_code', '')).strip()
    expiry = otp_context.get('expiry')
    intent = otp_context.get('intent')
    
    if time.time() > expiry:
        return JsonResponse({'success': False, 'message': 'کد منقضی شده است.'}, status=400)

    if user_code == session_code:
        
        # ==========================================
        # ۱. سناریوی ثبت‌ نام (Register)
        # ==========================================
        if intent == 'register':
            extra = otp_context.get('extra_data', {})
            try:
                # کپی کردن سبد خرید و URL ارجاعی قبل از لاگین
                pre_login_cart = request.session.get('cart', {})
                next_url = request.session.get('next_url', reverse('dashboard'))

                from .models import User, Province, City 
                province = Province.objects.get(id=extra['province_id'])
                city = City.objects.get(id=extra['city_id'])
                phone = otp_context['phone_number']
                
                # ساخت کاربر
                user = User(
                    first_name=extra['first_name'],
                    last_name=extra['last_name'],
                    phone_number=phone,
                    username=phone,
                    province=province,
                    city=city
                )
                if extra.get('password'): 
                    user.set_password(extra['password'])
                else: 
                    user.set_unusable_password()
                
                user.save()
                
                # جلوگیری از ارور Multiple Backends
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                
                # لاگین کردن و ادغام سبد خرید
                login(request, user)
                merge_session_cart(request, user, explicit_cart=pre_login_cart)
                
                
                # پاکسازی سشن
                request.session.pop('otp_context', None)
                request.session.pop('next_url', None)
                
                return JsonResponse({'success': True, 'redirect_url': next_url})
                
            except Exception as e:
                print(f"Registration Error: {e}")
                return JsonResponse({'success': False, 'message': f'خطای ثبت‌ نام: {str(e)}'}, status=500)
        
        # ==========================================
        # ۲. سناریوی ورود (Login)
        # ==========================================
        elif intent == 'login':
            try:
                phone = otp_context['phone_number']
                from .models import User
                user = User.objects.get(phone_number=phone)
                
                # ذخیره مقادیر قبل از لاگین
                pre_login_cart = request.session.get('cart', {})
                next_url = request.session.get('next_url', reverse('dashboard'))
                
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                # مرج کردن
                merge_session_cart(request, user, explicit_cart=pre_login_cart)
                
                # پاکسازی
                request.session.pop('otp_context', None)
                request.session.pop('next_url', None)
                
                return JsonResponse({'success': True, 'redirect_url': next_url})
                
            except Exception as e: 
                return JsonResponse({'success': False, 'message': 'حساب کاربری با این شماره یافت نشد.'}, status=404)
        
        # ==========================================
        # ۳. سناریوی فراموشی رمز عبور (Reset Password)
        # ==========================================
        elif intent == 'reset_password': 
            try:
                # ایجاد یک مجوز در سشن برای دسترسی به صفحه تغییر رمز
                request.session['can_reset_password'] = True
                request.session['reset_phone'] = otp_context['phone_number']
                
                # کد مصرف شده، پس کانتکست OTP را پاک می‌کنیم
                request.session.pop('otp_context', None)
                
                # ارجاع به صفحه اختصاصی ثبت رمز جدید
                return JsonResponse({'success': True, 'redirect_url': reverse('set_new_password_page')})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'خطایی در انتقال رخ داده است.'}, status=500)
            
    else:
        return JsonResponse({'success': False, 'message': 'کد نادرست است.'}, status=400)
    
def set_new_password_page(request):
    """صفحه تنظیم رمز عبور جدید با استفاده از Django Form"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    # محافظت امنیتی: کاربر حتماً باید از مرحله OTP با موفقیت رد شده باشد
    if not request.session.get('can_reset_password'):
        messages.error(request, "دسترسی غیرمجاز. لطفاً مجدداً تلاش کنید.")
        return redirect('auth')
        
    phone = request.session.get('reset_phone')
    
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        
        if form.is_valid():
            try:
                user = User.objects.get(phone_number=phone)
                user.set_password(form.cleaned_data['password'])
                user.save()
                
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                
                # بازیابی مقادیر موقت از سشن (برای ریدایرکت‌های هوشمند)
                pre_login_cart = request.session.get('cart', {})
                next_url = request.session.get('next_url', reverse('dashboard'))
                
                # لاگین خودکار پس از تغییر رمز
                login(request, user)
                merge_session_cart(request, user, explicit_cart=pre_login_cart)
                
                # پاکسازی ایمن تمام مجوزها و سشن‌های موقت
                request.session.pop('can_reset_password', None)
                request.session.pop('reset_phone', None)
                request.session.pop('next_url', None)
                
                messages.success(request, "رمز عبور با موفقیت تغییر کرد و وارد حساب شدید.")
                return redirect(next_url)
                
            except User.DoesNotExist:
                form.add_error(None, "متاسفانه کاربری با این شماره در دیتابیس یافت نشد.")
    else:
        form = SetNewPasswordForm()
                
    return render(request, 'auth_reset_password.html', {'form': form})

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
    
@require_POST
def request_otp_api(request):
    """API درخواست ارسال کد OTP برای ورود یا فراموشی رمز از صفحه لاگین"""
    try:
        data = json.loads(request.body)
        phone = str(data.get('phone_number', '')).strip()
        intent = str(data.get('intent', '')).strip()
    except:
        return JsonResponse({'success': False, 'message': 'فرمت نامعتبر'}, status=400)
        
    if not phone or intent not in ['login', 'reset_password']:
        return JsonResponse({'success': False, 'message': 'داده‌ها ناقص است.'}, status=400)

    # تبدیل اعداد فارسی به انگلیسی
    translation_table = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    phone = phone.translate(translation_table)

    # بررسی وجود کاربر (فقط کاربران ثبت‌نام شده می‌توانند بازیابی رمز یا ورود با کد کنند)
    if not User.objects.filter(phone_number=phone).exists():
        return JsonResponse({
            'success': False, 
            'message': 'حساب کاربری با این شماره یافت نشد. لطفاً ابتدا ثبت‌نام کنید.'
        }, status=404)

    # استفاده از موتور ماژولار OTP
    result = initiate_otp_process(request, phone_number=phone, intent=intent)
    
    if result['success'] or result.get('rate_limited'):
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'message': result['message']}, status=500)

from django.shortcuts import render, get_object_or_404
from .models import Product
from django.db.models import Q


def product_detail(request, slug):
    # دریافت محصول فعال
    product = get_object_or_404(Product, slug=slug, active_status=True)
    
    user_fingerprint = get_client_fingerprint(request)
    view_key = f"viewed:product:{product.id}:fp:{user_fingerprint}" # type: ignore
    
    if not cache.get(view_key):
        cache.set(view_key, True, timeout=86400) 
        
        Product.objects.filter(pk=product.id).update(visit_count=F('visit_count') + 1) # type: ignore

    # 2. بررسی وضعیت سبد خرید (آیا محصول در سبد هست؟ مقدارش چقدره؟)
    in_cart = False
    current_qty = 0
    
    if request.user.is_authenticated:
        # جستجو در سفارش باز (CART)
        item = OrderItem.objects.filter(
            order__customer=request.user, 
            order__status='CART', 
            product=product
        ).first()
        
        if item:
            in_cart = True
            current_qty = item.quantity
    else:
        # جستجو در سشن
        cart = request.session.get('cart', {})
        if str(product.id) in cart:
            in_cart = True
            current_qty = cart[str(product.id)]['quantity']

    # 3. محصولات مرتبط (کدهای قبلی شما)
    current_types = product.components.values_list('pistachio_type', flat=True)
    base_query = Product.objects.filter(active_status=True).exclude(id=product.id)

    if not product.is_mixed:
        cat1 = list(base_query.filter(is_mixed=False, components__pistachio_type__in=current_types).distinct().order_by('-visit_count'))
        cat2 = list(base_query.filter(is_mixed=True, components__pistachio_type__in=current_types).distinct().order_by('-visit_count'))
    else:
        cat1 = list(base_query.filter(is_mixed=True, components__pistachio_type__in=current_types).distinct().order_by('-visit_count'))
        cat2 = list(base_query.filter(is_mixed=False, components__pistachio_type__in=current_types).distinct().order_by('-visit_count'))

    final_list = []
    final_list.extend(cat1[:3])
    final_list.extend(cat2[:3])
    
    if len(final_list) < 4:
        needed = 6 - len(final_list)
        existing_ids = [p.id for p in final_list] + [product.id]
        populars = list(Product.objects.filter(active_status=True).exclude(id__in=existing_ids).order_by('-visit_count')[:needed])
        final_list.extend(populars)

    related_products = final_list[:6]

    # محاسبه سایز کارت "مشاهده بیشتر"
    count = len(related_products)
    remainder = count % 3
    
    if remainder == 0:
        see_more_span = "span-3"
    elif remainder == 1:
        see_more_span = "span-2"
    else:
        see_more_span = "span-1"

    context = {
        'product': product,
        'related_products': related_products,
        'see_more_span': see_more_span,
        'in_cart': in_cart,       # برای وضعیت اولیه دکمه
        'current_qty': current_qty, # برای پر کردن اینپوت تعداد/وزن
    }
    return render(request, 'product_detail.html', context)

def aboutus_page(request):
    return render(request,"about_us.html")
def shop_page(request):
    return render(request,"developing.html",{"message":"ما در حال طراحی، برنامه‌نویسی و آماده‌سازی صفحه فروشگاه از پستیلاین هستیم تا تجربه بی‌نظیری را برای شما رقم بزنیم. به زودی با امکانات جدید در این صفحه میزبان شما خواهیم بود"})

# ==========================================
# صفحه ۱: سبد خرید (Cart Page)
# ==========================================
def cart_page(request):
    cart_items = []
    total_price = 0
    all_free_shipping = True
    is_empty = True

    if request.user.is_authenticated:
        order = Order.objects.filter(customer=request.user, status='CART').first()
        if order and order.items.exists():
            is_empty = False
            for item in order.items.all():
                item_total = item.get_cost()
                total_price += item_total
                if not item.product.is_free_shipping:
                    all_free_shipping = False
                cart_items.append({
                    'product': item.product,
                    'quantity': item.quantity,
                    'total_cost': item_total,
                })
    else:
        session_cart = request.session.get('cart', {})
        if session_cart:
            is_empty = False
            for pid, data in session_cart.items():
                try:
                    product = Product.objects.get(id=pid)
                    
                    # ==== بخش اصلاح شده ====
                    # مقدار سشن را به استرینگ و سپس به دسیمال تبدیل می‌کنیم تا باگ float پیش نیاید
                    quantity_decimal = Decimal(str(data['quantity']))
                    item_total = product.price * quantity_decimal
                    # =======================
                    
                    total_price += item_total
                    if not product.is_free_shipping:
                        all_free_shipping = False
                    cart_items.append({
                        'product': product,
                        'quantity': data['quantity'],
                        'total_cost': item_total,
                    })
                except Product.DoesNotExist:
                    continue

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'all_free_shipping': all_free_shipping and not is_empty,
        'is_empty': is_empty,
    }
    return render(request, 'cart.html', context)

@require_POST
def update_cart_api(request):
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        action = data.get('action') # 'add', 'remove', 'update'
        quantity = float(data.get('quantity', 1))
    except:
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    in_cart = False
    cart_count = 0
    total_price = 0
    item_total = 0
    all_free_shipping = True

    if request.user.is_authenticated:
        order, _ = Order.objects.get_or_create(customer=request.user, status='CART')
        
        if action == 'remove':
            OrderItem.objects.filter(order=order, product_id=product_id).delete()
            in_cart = False
        else:
            product = get_object_or_404(Product, id=product_id)
            item, created = OrderItem.objects.get_or_create(
                order=order, product=product,
                defaults={'quantity': quantity, 'price': product.price}
            )
            if not created or action == 'update':
                item.quantity = quantity
                item.save()
            in_cart = True
            item_total = item.get_cost()
        
        order.calculate_total()
        total_price = order.total_price
        cart_count = order.items.count()
        
        # چک کردن ارسال رایگان کل سبد
        for i in order.items.all():
            if not i.product.is_free_shipping:
                all_free_shipping = False
                break
        if cart_count == 0: all_free_shipping = False

    else:
        cart = request.session.get('cart', {})
        if action == 'remove':
            if product_id in cart: del cart[product_id]
            in_cart = False
        else:
            cart[product_id] = {'quantity': quantity}
            in_cart = True
            
        request.session['cart'] = cart
        request.session.modified = True
        cart_count = len(cart)

        # محاسبه دستی برای کاربر مهمان
        for pid, c_data in cart.items():
            try:
                p = Product.objects.get(id=pid)
                qty = Decimal(str(c_data['quantity']))
                line_total = p.price * qty
                total_price += line_total
                if str(pid) == product_id:
                    item_total = line_total
                if not p.is_free_shipping:
                    all_free_shipping = False
            except: pass
        if cart_count == 0: all_free_shipping = False

    return JsonResponse({
        'success': True,
        'in_cart': in_cart,
        'cart_count': cart_count,
        'item_total': float(item_total),
        'total_price': float(total_price),
        'all_free_shipping': all_free_shipping
    })
# ==========================================
# صفحه ۲: اطلاعات ارسال (Checkout Page)
# ==========================================
from .forms import CheckoutForm # این را در بالای فایل ایمپورت کنید

@login_required(login_url='/auth/?next=/checkout/')
def checkout_page(request):
    order = Order.objects.filter(customer=request.user, status='CART').first()
    
    # اگر سبد خالی بود
    if not order or not order.items.exists():
        return redirect('cart_page')

    # چک کردن ارسال رایگان
    all_free_shipping = True
    for item in order.items.all():
        if not item.product.is_free_shipping:
            all_free_shipping = False
            break

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        
        if form.is_valid():
            cd = form.cleaned_data
            
            # ثبت اطلاعات گیرنده
            if cd['is_self_receiver']:
                order.receiver_name = request.user.get_full_name()
                order.receiver_phone = request.user.phone_number
            else:
                order.receiver_name = cd['receiver_name']
                order.receiver_phone = cd['receiver_phone']

            order.address = cd['address']
            order.postal_code = cd['postal_code']
            order.shipping_cost = 0 # فعلاً 0 تا تماس گرفته شود
            
            # تغییر وضعیت سفارش (ثبت نهایی)
            order.status = 'PENDING'
            order.save()

            # ذخیره آدرس برای دفعات بعد اگر کاربر تایید کرده بود
            if cd.get('save_info'):
                request.user.address = cd['address']
                request.user.postal_code = cd['postal_code']
                request.user.save()

            return redirect('order_success', order_number=order.order_number)
        
        else:
            # اگر فرم نامعتبر بود، ارورها را به صورت Message به کاربر نشان می‌دهیم
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CheckoutForm()

    context = {
        'order': order,
        'all_free_shipping': all_free_shipping,
        'user': request.user,
    }
    return render(request, 'checkout.html', context)

# --- تابع order_success_page ---
@login_required(login_url='auth')
def order_success_page(request, order_number):
    # جستجو بر اساس order_number اختصاصی
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    return render(request, 'order_success.html', {'order': order})

def ai_page(request):
    return render(request,"developing.html",{"message":"ما در حال طراحی، برنامه‌نویسی و آماده‌سازی هوش مصنوعی پستیلاین هستیم تا تجربه بی‌نظیری را برای شما رقم بزنیم. به زودی با امکانات جدید در این صفحه میزبان شما خواهیم بود"})

def mixer_page(request):
    return render(request,"developing.html")

def maintenance_page(request):
    settings = SiteSettings.objects.first()
    return render(request, 'maintenance.html', {'message': settings.maintenance_message}) # type: ignore

def developing_page(request):
    return render(request,"developing.html")

def commingsoon_page(request):
    settings = SiteSettings.objects.first()
    from resume.models import Resume
    from django.utils import timezone

    context = {'target_date': settings.coming_soon_date}
    if settings.coming_soon_date:
        remaining = settings.coming_soon_date - timezone.now()
        if remaining.total_seconds() > 0:
            context['is_expired'] = False
        else:
            context['is_expired'] = True
    settings = SiteSettings.objects.first()
    context['site_settings'] = settings
    context['team_members'] = Resume.objects.filter(is_confirmed=True).order_by('-id')[:6]
    return render(request, 'coming_soon.html', context)

def dashboard_page(request):
    return render(request,"developing.html")