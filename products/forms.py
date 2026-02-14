from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import User, Province, City  # فرض بر این است که مدل‌ها در همین اپ هستند

# ==========================================
# 1. تعریف اعتبارسنج‌های سراسری (Validators)
# ==========================================

# فقط حروف فارسی و فاصله مجاز است
farsi_validator = RegexValidator(
    regex=r'^[\u0600-\u06FF\s]+$',
    message='لطفاً فقط از حروف فارسی استفاده کنید.'
)

# پسورد پیچیده: حداقل ۶ کاراکتر، شامل حروف انگلیسی و (عدد یا کاراکتر خاص)
password_complexity_validator = RegexValidator(
    regex=r'^(?=.*[a-zA-Z])(?=.*[0-9!@#$%^&*]).{6,}$',
    message='رمز عبور باید حداقل ۶ کاراکتر و ترکیبی از حروف انگلیسی و اعداد/علائم باشد.'
)

class UserRegisterForm(forms.ModelForm):
    # فیلدهای اضافی که مستقیماً در مدل User نیستند یا نیاز به تنظیمات خاص دارند
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'تکرار رمز عبور'}),
        required=False,
        label="تکرار رمز عبور"
    )
    
    # فیلد چک‌باکس برای درخواست ورود با OTP
    otp_request = forms.BooleanField(
        required=False, 
        widget=forms.CheckboxInput()
    )
    
    # فیلدهای استان و شهر (به صورت مدل چیس برای دریافت ID)
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(), 
        required=True, 
        error_messages={'required': 'لطفاً استان را انتخاب کنید.'}
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.all(), 
        required=True, 
        error_messages={'required': 'لطفاً شهر را انتخاب کنید.'}
    )

    # فیلد پسورد را بازنویسی می‌کنیم تا ویژگی‌های HTML را اضافه کنیم
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'رمز عبور'}),
        required=False,
        label="رمز عبور"
    )

    class Meta:
        model = User
        # فیلد username را در فرم نمی‌آوریم
        fields = ['first_name', 'last_name', 'phone_number', 'province', 'city']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # اعمال اعتبارسنجی حروف فارسی روی نام و نام خانوادگی
        self.fields['first_name'].validators.append(farsi_validator)
        self.fields['first_name'].min_length = 3
        self.fields['first_name'].required = True
        
        self.fields['last_name'].validators.append(farsi_validator)
        self.fields['last_name'].min_length = 3
        self.fields['last_name'].required = True

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # ۱. تبدیل اعداد فارسی به انگلیسی
            translation_table = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
            phone = phone.translate(translation_table)
            
            # ۲. بررسی فرمت کلی (چون در مدل RegexValidator دارید، اینجا هم محض اطمینان چک می‌کنیم یا به مدل می‌سپاریم)
            # اما چون Unique بودن را باید قبل از ذخیره چک کنیم:
            if User.objects.filter(phone_number=phone).exists():
                raise ValidationError('این شماره تلفن قبلاً ثبت شده است.')
                
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        otp_request = cleaned_data.get('otp_request')

        # منطق شرطی: اگر تیک OTP زده شده، پسورد نیاز نیست. در غیر این صورت اجباری است.
        if otp_request:
            # اگر پسورد وارد شده بود اما تیک OTP هم زده بود، پسورد را نادیده می‌گیریم
            if 'password' in cleaned_data:
                del cleaned_data['password']
        else:
            # حالت عادی: پسورد اجباری است
            if not password:
                self.add_error('password', 'وارد کردن رمز عبور الزامی است.')
            else:
                # بررسی پیچیدگی پسورد
                try:
                    password_complexity_validator(password)
                except ValidationError as e:
                    self.add_error('password', e.message)

                # بررسی تطابق دو پسورد
                if password != confirm_password:
                    self.add_error('confirm_password', 'رمز عبور و تکرار آن مطابقت ندارند.')
        
        return cleaned_data

    def save(self, commit=True):
        # ساخت نمونه کاربر بدون ذخیره در دیتابیس
        user = super().save(commit=False)
        
        # نکته مهم: پر کردن فیلد username با شماره موبایل (چون در AbstractUser اجباری است)
        user.username = self.cleaned_data['phone_number']
        
        # تنظیم پسورد
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        else:
            # اگر با OTP ثبت‌نام می‌کند، پسورد غیرقابل استفاده ست می‌شود
            user.set_unusable_password()
            
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    phone_number = forms.CharField(
        max_length=11, 
        label="شماره همراه",
        widget=forms.TextInput(attrs={'placeholder': '09123456789'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '******'}),
        label="رمز عبور"
    )

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # تبدیل اعداد فارسی به انگلیسی برای لاگین صحیح
            translation_table = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
            phone = phone.translate(translation_table)
        return phone