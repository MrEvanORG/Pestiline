from .models import CustomSeoData

def seo_processor(request):
    path = request.path
    seo_data = CustomSeoData.objects.filter(path=path).first()
    if seo_data:
        return {"seo_title":seo_data.title,"seo_description":seo_data.meta_description}
    return {}