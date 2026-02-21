import json
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from decimal import Decimal
from .forms import UserRegisterForm, UserLoginForm
from .models import User, Province, City, Product, Order, OrderItem
from .addons import initiate_otp_process, get_otp_settings, get_remaining_otp_time
# ... (صفحات عمومی بدون تغییر) ...
def index_page(request): return render(request, 'index.html')
@login_required(login_url='auth')
def dashboard_page(request): return HttpResponse(f"خوش آمدید {request.user.first_name}!")

def get_cart_count(request):
    """محاسبه تعداد اقلام در سبد خرید فعال (وضعیت CART)"""
    if request.user.is_authenticated:
        order = Order.objects.filter(customer=request.user, status='CART').first()
        return order.items.count() if order else 0
    else:
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
    """API برای افزودن، حذف و آپدیت تعداد آیتم‌های سبد"""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        action = data.get('action') # 'add', 'remove', 'update'
        quantity = float(data.get('quantity', 1))
    except:
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    in_cart = False

    # === سناریوی کاربر لاگین شده (دیتابیس) ===
    if request.user.is_authenticated:
        # دریافت یا ساخت سبد خرید (وضعیت CART)
        order, _ = Order.objects.get_or_create(customer=request.user, status='CART')
        
        if action == 'remove':
            OrderItem.objects.filter(order=order, product_id=product_id).delete()
            in_cart = False
        else: 
            # برای add و update
            product = get_object_or_404(Product, id=product_id)
            item, created = OrderItem.objects.get_or_create(
                order=order, 
                product=product,
                defaults={'quantity': quantity, 'price': product.price}
            )
            
            # اگر آیتم از قبل بود یا درخواست آپدیت صریح داشتیم، مقدار را بروز کن
            if not created or action == 'update':
                item.quantity = quantity
                item.save()
            
            in_cart = True
        
        order.calculate_total()
        cart_count = order.items.count()

    # === سناریوی کاربر مهمان (سشن) ===
    else:
        cart = request.session.get('cart', {})
        
        if action == 'remove':
            if product_id in cart:
                del cart[product_id]
            in_cart = False
        else: 
            # برای add و update مقدار را ست میکنیم
            cart[product_id] = {'quantity': quantity}
            in_cart = True
        
        request.session['cart'] = cart
        request.session.modified = True
        cart_count = len(cart)

    return JsonResponse({
        'success': True,
        'in_cart': in_cart,     # وضعیت نهایی محصول (در سبد هست یا نه)
        'cart_count': cart_count, # تعداد کل اقلام سبد برای بج هدر
        'message': 'سبد خرید بروز شد'
    })
# ==========================================
# سیستم احراز هویت ماژولار
# ==========================================
def auth_page(request):

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
                    merge_session_cart(request, user)
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

    # دریافت کانتکست قبل از هر کاری
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
                # 1. کپی کردن سبد خرید قبل از اینکه لاگین سشن را تغییر دهد
                pre_login_cart = request.session.get('cart', {})

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
                
                # جلوگیری از ارور Multiple Backends
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                
                # 2. انجام لاگین (اینجا سشن ممکن است ریست شود)
                login(request, user)
                
                # 3. فراخوانی مرج با سبد خریدی که کپی کرده بودیم
                merge_session_cart(request, user, explicit_cart=pre_login_cart)
                
                # 4. پاک کردن امن کانتکست (با pop که ارور ندهد)
                request.session.pop('otp_context', None)
                
                return JsonResponse({'success': True, 'redirect_url': reverse('dashboard')})
                
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'خطای ثبت‌ نام: {str(e)}'}, status=500)
        
        elif intent == 'login':
            # همین منطق را برای لاگین با OTP هم می‌توانید پیاده کنید
            return JsonResponse({'success': True, 'redirect_url': reverse('dashboard')})
            
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
    
from django.shortcuts import render, get_object_or_404
from .models import Product
from django.db.models import Q


def product_detail(request, slug):
    # دریافت محصول فعال
    product = get_object_or_404(Product, slug=slug, active_status=True)
    
    # 1. منطق بازدید (Session Based)
    session_key = f'viewed_product_{product.id}'
    if not request.session.get(session_key, False):
        product.visit_count += 1
        product.save()
        request.session[session_key] = True

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
    return HttpResponse("about us")