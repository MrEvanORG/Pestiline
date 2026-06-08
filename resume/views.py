from .models import Resume
from django.db.models import F
from .forms import ContactForm
from django.core.cache import cache
from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse 
from django.shortcuts import redirect 
from django.urls import reverse
from .addons import generate_captcha_image
from products.models import NotificationLog 
from django.shortcuts import get_object_or_404
from products.addons import get_client_fingerprint
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

def captcha_view(request):
    text, image_bytes = generate_captcha_image()
    request.session['captcha_text'] = text
    return HttpResponse(image_bytes, content_type="image/png")

def resume_detail_view(request, slug):
    resume_object = get_object_or_404(Resume, slug=slug, is_confirmed=True)

    user_fingerprint = get_client_fingerprint(request)
    view_key = f"viewed:resume:{resume_object.id}:fp:{user_fingerprint}" # type: ignore
    
    if not cache.get(view_key):
        cache.set(view_key, True, timeout=86400) 
        
        Resume.objects.filter(pk=resume_object.id).update(visit_count=F('visit_count') + 1) # type: ignore

    skills_1_list = []
    if resume_object.skills_category_1:
        skills = resume_object.skills_category_1.strip().strip(';').split(';')
        for skill_pair in skills:
            if skill_pair and ',' in skill_pair:
                skills_1_list.append(skill_pair.split(','))
    
    resume_object.processed_skills_1 = skills_1_list # type: ignore

    skills_2_list = []
    if resume_object.skills_category_2:
        skills = resume_object.skills_category_2.strip().strip(';').split(';')
        for skill_pair in skills:
            if skill_pair and ',' in skill_pair:
                skills_2_list.append(skill_pair.split(','))

    resume_object.processed_skills_2 = skills_2_list # type: ignore

    if request.method == 'POST':
        form = ContactForm(request.POST, request=request)
        if form.is_valid():
            name = form.cleaned_data['name']
            reply_to = form.cleaned_data['reply_to']
            user_message = form.cleaned_data['message']
            
            if not resume_object.related_user.email:
                messages.error(request, "متأسفانه مشکلی در ارسال ایمیل رخ داد. بعداً تلاش کنید.")
                return render(request, 'resum.html', {'resume': resume_object, 'form': form})

            subject = f"پیام جدید از فرم رزومه: {name}"
            recipient_list = [resume_object.related_user.email]
            
            # تغییر اصلی: ساختار جدید کانتکست برای هماهنگی با قالب ماژولار مادر
            email_context = {
                'subject': subject,
                'main_title': 'پیام جدید دریافت شد',
                'top_greeting': 'کاربر گرامی،',
                'top_message': f'شما یک پیام جدید از طرف "{name}" در رابطه با رزومه خود دریافت کرده‌اید.',
                'info_box_title': 'اطلاعات تماس فرستنده',
                'info_items': [
                    {'label': 'نام فرستنده', 'value': name, 'is_link': False},
                    {'label': 'راه ارتباطی (ایمیل)', 'value': reply_to, 'is_link': False}
                ],
                'user_message': user_message, # متن پیام کاربر در باکس پایینی می‌نشیند
                'cta_text': 'مشاهده رزومه در سایت',
                'cta_link': request.build_absolute_uri(
                    reverse('resume_detail', kwargs={'slug': slug})
                )
            }
            
            html_message = render_to_string('products/emails/base_email.html', email_context)
            plain_message = f"نام فرستنده: {name}\nتماس: {reply_to}\n\nمتن پیام:\n{user_message}"

            try:
                email = EmailMultiAlternatives(
                    subject,
                    plain_message,      
                    None,               
                    recipient_list,
                    reply_to=[reply_to] 
                )
                email.attach_alternative(html_message, "text/html") 
                email.send()
                
                NotificationLog.objects.create(
                    user=resume_object.related_user,
                    notification_type='EMAIL',
                    related_event=NotificationLog.EventChoices.NEW_RESUMEMSG_TA,
                    message_content=plain_message,
                    status='SUCCESS'
                )
                
                messages.success(request, "پیام شما با موفقیت ارسال شد.")
                url = reverse('resume_detail', kwargs={'slug': slug}) + '#contact'
                return redirect(url) 
            
            except Exception as e:
                NotificationLog.objects.create(
                    user=resume_object.related_user,
                    notification_type='EMAIL',
                    related_event=NotificationLog.EventChoices.NEW_RESUMEMSG_TA,
                    message_content=plain_message,
                    status='FAILED',
                    error_details=str(e)[:200] 
                )
                messages.error(request, "متأسفانه مشکلی در ارسال ایمیل رخ داد. بعداً تلاش کنید.")
    else:
        form = ContactForm()
    
    context = {
        'resume': resume_object,
        'form': form,
    }
    return render(request, 'resum.html', context)