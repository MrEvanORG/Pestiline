document.addEventListener('DOMContentLoaded', function() {
    // مقادیری که نیاز به آپلود عکس دارند
    const imageRequiredTypes = ['image', 'gallery', 'banner'];

    // تابع اصلی برای نمایش/مخفی کردن
    function toggleImageVisibility(inlineRow, blockTypeValue) {
        // کلاس‌هایی که جنگو به صورت خودکار به فیلدها می‌دهد
        const imageField = inlineRow.querySelector('.field-image');
        const imagePreviewField = inlineRow.querySelector('.field-image_preview'); 

        const needsImage = imageRequiredTypes.includes(blockTypeValue);

        if (imageField) {
            imageField.style.display = needsImage ? '' : 'none';
        }
        if (imagePreviewField) {
            imagePreviewField.style.display = needsImage ? '' : 'none';
        }
    }

    // ۱. اعمال روی بلاک‌های موجود هنگام لود صفحه
    const selects = document.querySelectorAll('select[name$="-block_type"]');
    selects.forEach(select => {
        const row = select.closest('.inline-related');
        if (row) {
            toggleImageVisibility(row, select.value);
        }
    });

    // ۲. اعمال هنگام تغییر نوع بلاک (Event Delegation)
    document.addEventListener('change', function(e) {
        if (e.target.matches('select[name$="-block_type"]')) {
            const row = e.target.closest('.inline-related');
            if (row) {
                toggleImageVisibility(row, e.target.value);
            }
        }
    });

    // ۳. اعمال روی بلاک‌های جدیدی که با دکمه "افزودن" ساخته می‌شوند
    document.addEventListener('formset:added', (event) => {
        const row = event.target;
        const select = row.querySelector('select[name$="-block_type"]');
        if (select) {
            toggleImageVisibility(row, select.value);
        }
    });
});
