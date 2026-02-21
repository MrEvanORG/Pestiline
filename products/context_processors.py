from .models import SiteSettings , Order

def site_settings(request):
    settings = SiteSettings.objects.first()
    return {'site_settings': settings}

def cart_context(request):
    """محاسبه تعداد آیتم‌های سبد خرید برای تمام صفحات"""
    count = 0
    if request.user.is_authenticated:
        # دریافت سفارش با وضعیت CART
        order = Order.objects.filter(customer=request.user, status='CART').first()
        if order:
            count = order.items.count()
    else:
        # دریافت از سشن
        cart = request.session.get('cart', {})
        count = len(cart)
    
    return {'cart_count': count}