from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Resume
def resume_detail_view(request, slug):
    # ۱. رزومه مورد نظر را پیدا می‌کنیم
    resume_object = get_object_or_404(Resume,slug=slug, is_confirmed=True)

    # ۲. پردازش مهارت‌های دسته اول
    skills_1_list = []
    if resume_object.skills_category_1:
        # با strip(';') مطمئن می‌شویم سمی‌کالن اضافه در ابتدا یا انتها حذف شود
        skills = resume_object.skills_category_1.strip().strip(';').split(';')
        for skill_pair in skills:
            if skill_pair and ',' in skill_pair:
                skills_1_list.append(skill_pair.split(','))
    
    # یک ویژگی جدید به آبجکت اضافه می‌کنیم
    resume_object.processed_skills_1 = skills_1_list

    # ۳. پردازش مهارت‌های دسته دوم
    skills_2_list = []
    if resume_object.skills_category_2:
        skills = resume_object.skills_category_2.strip().strip(';').split(';')
        for skill_pair in skills:
            if skill_pair and ',' in skill_pair:
                skills_2_list.append(skill_pair.split(','))

    resume_object.processed_skills_2 = skills_2_list
    
    # ۴. آبجکت کامل شده را به تمپلیت ارسال می‌کنیم
    context = {
        'resume': resume_object,
    }
    return render(request, 'resum.html', context)
