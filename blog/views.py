from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from .models import BlogPost, Category

class BlogIndexView(ListView):
    model = BlogPost
    template_name = 'index.html'
    context_object_name = 'posts'
    paginate_by = 12 # نمایش 12 مقاله در هر صفحه

    def get_queryset(self):
        # select_related برای کلیدهای خارجی (author, category)
        return BlogPost.objects.filter(is_published=True)\
            .select_related('category', 'author')\
            .order_by('-created_at')

class CategoryDetailView(ListView):
    template_name = 'category_detail.html'
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
        return context

class PostDetailView(DetailView):
    model = BlogPost
    template_name = 'post_detail.html'
    context_object_name = 'post'

    def get_object(self):
        # prefetch_related برای ManyToMany و فیلدهای Reverse (تگ‌ها و بلاک‌ها)
        return get_object_or_404(
            BlogPost.objects.select_related('category', 'author')
            .prefetch_related('blocks', 'tags'),
            category__slug=self.kwargs['category_slug'],
            slug=self.kwargs['post_slug'],
            is_published=True
        )
