import re
import random
import string
import io
import os
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings

def persian_slugify(value):
    value = re.sub(r'[\u200c\u200b\u200d\uFEFF]', '',value)
    
    value = str(value).strip()

    value = re.sub(r'[^\w\s\-ا-ی]', '', value)

    value = re.sub(r'[\s‌]+', ' ', value)

    value = re.sub(r'\s+', '-', value)

    return value.strip('-')


def generate_captcha_image():
    # ۱. تولید عدد ۶ رقمی تصادفی
    captcha_text = ''.join(random.choices(string.digits, k=6))
    
    # ۲. تنظیمات تصویر
    width, height = 170, 50
    # ایجاد یک تصویر با پس‌زمینه روشن
    image = Image.new('RGB', (width, height), color='#dae9c3')
    draw = ImageDraw.Draw(image)
    
    font_path = os.path.join(settings.BASE_DIR,'products','static','products','fonts','Vazirmatn-Medium.woff2')
    
    try:
        font = ImageFont.truetype(font_path, 32)
    except:
        print("font didnt find",font_path)
        font = ImageFont.load_default()

    # ۴. کشیدن متن روی تصویر (کمی مخدوش و نامنظم)
    for i, char in enumerate(captcha_text):
        # ایجاد کمی جابجایی برای هر کاراکتر
        pos = (15 + (i * 20), random.randint(5, 15))
        draw.text(pos, char, fill='#123524', font=font)

    # ۵. افزودن خطوط اضافی برای مخدوش کردن (Anti-Bot)
    for _ in range(5):
        draw.line([(random.randint(0, width), random.randint(0, height)), 
                   (random.randint(0, width), random.randint(0, height))], 
                  fill=(200, 200, 200), width=1)

    # ۶. ذخیره در حافظه موقت (Buffer)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    
    return captcha_text, buffer.getvalue()

