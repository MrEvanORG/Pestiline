from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'برنامه وبلاگ'
    def ready(self):
        # ایمپورت کردن سیگنال‌ها هنگام لود شدن اپلیکیشن
        import blog.signals
