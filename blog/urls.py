from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # صفحه اصلی وبلاگ (لیست همه مقالات)
    path('', views.BlogIndexView.as_view(), name='blog_index'),
    
    # صفحه دسته‌بندی خاص (مثلا /blog/technology/)
    path('<str:category_slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # صفحه جزئیات مقاله (مثلا /blog/technology/how-to-code/)
    path('<slug:category_slug>/<slug:post_slug>/', views.PostDetailView.as_view(), name='post_detail'),
]
