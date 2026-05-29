from django import forms
import re

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, error_messages={'required': 'لطفاً نام خود را وارد کنید.'})
    reply_to = forms.CharField(max_length=100, error_messages={'required': 'لطفاً ایمیل یا شماره تماس خود را وارد کنید.'})
    message = forms.CharField(widget=forms.Textarea, error_messages={'required': 'متن پیام نمی‌تواند خالی باشد.'})
    captcha = forms.CharField(max_length=6, error_messages={'required': 'کد امنیتی را وارد کنید.'})

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ContactForm, self).__init__(*args, **kwargs)

    # اصلاح نام متد و فیلد
    def clean_reply_to(self):
        data = self.cleaned_data.get('reply_to')
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        phone_regex = r'^09\d{9}$'

        if re.match(email_regex, data) or re.match(phone_regex, data):
            return data
        raise forms.ValidationError("لطفاً یک ایمیل معتبر یا شماره موبایل صحیح وارد کنید.")

    def clean_captcha(self):
        captcha_input = self.cleaned_data.get('captcha')
        captcha_session = self.request.session.get('captcha_text')

        if not captcha_session or captcha_input != captcha_session:
            raise forms.ValidationError("کد امنیتی وارد شده اشتباه است.")
        
        if 'captcha_text' in self.request.session:
            del self.request.session['captcha_text']
            
        return captcha_input
