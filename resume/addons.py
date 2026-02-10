import re

def persian_slugify(value):
    value = re.sub(r'[\u200c\u200b\u200d\uFEFF]', '',value)
    
    value = str(value).strip()

    value = re.sub(r'[^\w\s\-ا-ی]', '', value)

    value = re.sub(r'[\s‌]+', ' ', value)

    value = re.sub(r'\s+', '-', value)

    return value.strip('-')
