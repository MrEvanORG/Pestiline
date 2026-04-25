from .models import Resume
from django.db.models import F
from django.core.cache import cache
from django.shortcuts import render
from products.addons import get_client_fingerprint
from django.shortcuts import get_object_or_404

def resume_detail_view(request, slug):
    resume_object = get_object_or_404(Resume, slug=slug, is_confirmed=True)

    user_fingerprint = get_client_fingerprint(request)
    view_key = f"viewed:resume:{resume_object.id}:fp:{user_fingerprint}" # type: ignore
    
    if not cache.get(view_key):
        cache.set(view_key, True, timeout=86400) 
        
        Resume.objects.filter(pk=resume_object.id).update(visit_count=F('visit_count') + 1) # type: ignore

    skills_1_list = []
    if resume_object.skills_category_1:
        skills = resume_object.skills_category_1.strip().strip(';').split(';')
        for skill_pair in skills:
            if skill_pair and ',' in skill_pair:
                skills_1_list.append(skill_pair.split(','))
    
    resume_object.processed_skills_1 = skills_1_list # type: ignore

    skills_2_list = []
    if resume_object.skills_category_2:
        skills = resume_object.skills_category_2.strip().strip(';').split(';')
        for skill_pair in skills:
            if skill_pair and ',' in skill_pair:
                skills_2_list.append(skill_pair.split(','))

    resume_object.processed_skills_2 = skills_2_list # type: ignore
    
    context = {
        'resume': resume_object,
    }
    return render(request, 'resum.html', context)
