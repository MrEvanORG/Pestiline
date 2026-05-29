"""
Django settings for pestiline project.
using Django 6.0.1.
"""
# accpeted max lenght = 250
import os
from pathlib import Path
from decouple import config
# ------------------------ BaseSettings ------------------------#
BASE_DIR = Path(__file__).resolve().parent.parent

DEV_MODE = config('DEV_MODE',cast=bool)

DEBUG_HOST = config('DEBUG_HOST',cast=bool)

SMS_API = config('SMS_API')

SECRET_KEY = config('DJANGO_SECRET_KEY')

ADMIN_URL = config('ADMIN_URL')

SITEMAP_URL = config('SITEMAP_URL')

if DEV_MODE:
    DEBUG = True
else:
    if DEBUG_HOST:
        DEBUG = True
    else:
        DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1','10.33.117.235','192.168.1.11','www.pestiline.ir','pestiline.ir']

CSRF_TRUSTED_ORIGINS = ['https://www.pestiline.ir','https://pestiline.ir/']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps', 

    'products.apps.ProductsConfig',
    'resume.apps.ResumeConfig',
    'seo.apps.SeoConfig',

    'adminsortable2', 
    # pip install django-adminsortable2

    'blog.apps.BlogConfig',
    
    'django.contrib.humanize',
]

#--------------------------- Templates ------------------------#
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'products.middleware.SiteViewCounterMiddleware',#شمردن ویوهای سایت
    'products.middleware.SiteStatusMiddleware',
    
]

ROOT_URLCONF = 'pestiline.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'products.context_processors.site_settings',
                'products.context_processors.cart_context',
                'seo.context_processors.seo_processor'
            ],
        },
    },
]

WSGI_APPLICATION = 'pestiline.wsgi.application'

#---------------------------- Cashes --------------------------#
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_site_cache_table', # نام جدولی که جنگو می‌سازد
    }
}
# python manage.py createcachetable
#جایگزین ردیس موقت !
#--------------------------- Databases ------------------------#
# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
if DEV_MODE : 
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config("DATABASE_NAME", default=""),
            'USER': config("DATABASE_USER", default=""),
            'PASSWORD': config("DATABASE_PASSWORD", default=""),
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {
                'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'",
                'sql_mode': 'STRICT_TRANS_TABLES',
            },
        }
    }
# ALTER DATABASE `your_database_name` CHARACTER SET utf8mb4 COLLATE utf8mb4_persian_ci;
#------------------------ Authentications ---------------------#
# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'products.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    #بررسی لاگین توسط شماره تلفن نه یوزرنیم
    'products.backends.PhoneBackend', 
    # بک‌اند پیش‌فرض جنگو (برای اینکه ادمین پنل خراب نشود حتما باید باشد)
    'django.contrib.auth.backends.ModelBackend',
]

#------------------------- OnlyHTPPS -------------------------#
if not DEV_MODE : 
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSE_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTION = 'DENY'

    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


#----------------------- Persianolization ---------------------#
# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_L10N = True
USE_TZ = True
SITE_ID = 1

#-------------------------- StaticFiles -----------------------#
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
#----------------------------- Email --------------------------#
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT",cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_PASSWORD")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
