// ۱. نمایش/مخفی کردن رمز عبور
function showTab(type) {
    document.querySelectorAll('.auth-form, .tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(type + '-form').classList.add('active');
    event.currentTarget.classList.add('active');
}

function togglePassword(inputId, icon) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
        icon.classList.replace("fa-eye", "fa-eye-slash");
    } else {
        input.type = "password";
        icon.classList.replace("fa-eye-slash", "fa-eye");
    }
}

// ۲. انیمیشن حذف فیلدها هنگام انتخاب ورود دو مرحله‌ای
document.getElementById('otp-only').addEventListener('change', function() {
    const passwordSection = document.getElementById('password-section');
    const passInputs = passwordSection.querySelectorAll('input');
    
    if (this.checked) {
        passwordSection.classList.add('hidden-mode');
        // غیرفعال کردن Required برای ارسال فرم بدون پسورد
        passInputs.forEach(input => input.removeAttribute('required'));
    } else {
        passwordSection.classList.remove('hidden-mode');
        // فعال کردن مجدد Required
        passInputs.forEach(input => input.setAttribute('required', ''));
    }
});