from .models import BlogPost, Category
from django.shortcuts import get_object_or_404
from products.addons import get_client_fingerprint
from django.views.generic import ListView, DetailView
from django.db.models import F
from django.core.cache import cache

class BlogIndexView(ListView):
    model = BlogPost
    template_name = 'blog_index.html'
    context_object_name = 'posts'
    paginate_by = 12 # نمایش 12 مقاله در هر صفحه

    def get_queryset(self):
        # select_related برای کلیدهای خارجی (author, category)
        return BlogPost.objects.filter(is_published=True)\
            .select_related('category', 'author')\
            .order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # گرفتن تمام دسته‌بندی‌ها
        context['categories'] = Category.objects.all()
        return context

class CategoryDetailView(ListView):
    template_name = 'developing.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        return BlogPost.objects.filter(category=self.category, is_published=True)\
            .select_related('author', 'category')\
            .order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['message'] = "ما در حال طراحی، برنامه‌نویسی و آماده‌سازی وبلاگ پستیلاین هستیم بخشی از این وبلاگ در دست توسعه است . به زودی با امکانات جدید در این صفحه میزبان شما خواهیم بود"
        return context

class PostDetailView(DetailView):
    model = BlogPost
    template_name = 'post_detail.html'
    context_object_name = 'post'

    def get_object(self): # type: ignore
        return get_object_or_404(
            BlogPost.objects.select_related('category', 'author')
            .prefetch_related('blocks', 'tags'),
            category__slug=self.kwargs['category_slug'],
            slug=self.kwargs['post_slug'],
            is_published=True
        )

    def get(self, request, *args, **kwargs):

        response = super().get(request, *args, **kwargs)

        post_object = self.object  
        
        user_fingerprint = get_client_fingerprint(request)

        view_key = f"viewed:blogpost:{post_object.id}:fp:{user_fingerprint}"
        
        if not cache.get(view_key):
            cache.set(view_key, True, timeout=86400)
            BlogPost.objects.filter(pk=post_object.id).update(view_count=F('view_count') + 1)

        return response
