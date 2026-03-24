/**
 * Pestiline Reset Password Validation Logic
 * Fixed: Native Django ID/Name Compatibility & Real-time Validation
 */

document.addEventListener('DOMContentLoaded', () => {
    setupResetPasswordLogic();
});

// تابع عمومی برای تغییر آیکون چشم (کاملا مقاوم در برابر null)
window.togglePassword = (id, icon) => {
    const inp = document.getElementById(id);
    if (!inp) return; // جلوگیری از ارور null
    const isPassword = inp.type === "password";
    inp.type = isPassword ? "text" : "password";
    icon.classList.replace(isPassword ? "fa-eye-slash" : "fa-eye", isPassword ? "fa-eye" : "fa-eye-slash");
};

function setupResetPasswordLogic() {
    // پیدا کردن فیلدها با استفاده از Name استاندارد جنگو
    const passInput = document.querySelector('input[name="password"]');
    const confirmInput = document.querySelector('input[name="confirm_password"]');
    const btnSubmit = document.getElementById('btn-submit-reset');
    const formEl = document.getElementById('reset-password-form');

    if (!passInput || !confirmInput) return; // اطمینان از وجود فیلدها

    const inputs = [passInput, confirmInput];

    // اتصال رویدادها به اینپوت‌ها به صورت زنده (Live)
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            input.classList.add('touched'); 
            updateUI(input);
            triggerValidation();
            
            // چک کردن همزمان تکرار رمز، وقتی رمز اصلی تغییر می‌کند
            if (input.name === 'password' && confirmInput.value.length > 0) {
                updateUI(confirmInput);
            }
        });

        input.addEventListener('blur', () => {
            input.classList.add('touched');
            updateUI(input);
            triggerValidation();
        });
    });

    // جلوگیری از ارسال فرم در صورت نامعتبر بودن
    formEl.addEventListener('submit', (e) => {
        if (!checkFormValidity()) {
            e.preventDefault();
            inputs.forEach(i => {
                i.classList.add('touched');
                updateUI(i);
            });
        }
    });

    // ------------------------------------------
    // توابع ارزیابی
    // ------------------------------------------

    function triggerValidation() {
        if (checkFormValidity()) {
            btnSubmit.removeAttribute('disabled');
            btnSubmit.style.cursor = 'pointer';
        } else {
            btnSubmit.setAttribute('disabled', 'true');
            btnSubmit.style.cursor = 'not-allowed';
        }
    }

    function checkFormValidity() {
        for (let input of inputs) {
            if (getErrorMsg(input) !== "") return false;
        }
        return true;
    }

    function getErrorMsg(input) {
        const val = input.value.trim();
        const name = input.name; // استفاده از name به جای data-validate
        
        if (!val) return "لطفاً این فیلد را تکمیل کنید.";

        const strictPass = /^(?=.*[a-zA-Z])(?=.*[0-9!@#$%^&*]).{6,}$/;
        const hasPersian = /[\u0600-\u06FF]/;

        if (name === 'password') {
            if (hasPersian.test(val)) return "لطفاً کیبورد خود را انگلیسی کنید.";
            if (val.length < 6) return "رمز عبور باید حداقل ۶ کاراکتر باشد.";
            if (!strictPass.test(val)) return "ترکیبی از حروف انگلیسی و اعداد/علائم باشد.";
        } 
        else if (name === 'confirm_password') {
            const originalPass = passInput.value.trim();
            if (val !== originalPass) return "رمز عبور و تکرار آن یکسان نیستند.";
        }

        return "";
    }

    function updateUI(input) {
        const msg = getErrorMsg(input);
        // پیدا کردن اسپَن ارور متناظر با نام فیلد
        const errEl = document.getElementById('error-' + input.name);

        if (errEl) {
            errEl.textContent = msg;
            if (msg !== "") {
                errEl.classList.add('show');
                input.classList.add('invalid');
            } else {
                errEl.classList.remove('show');
                input.classList.remove('invalid');
            }
        }
    }

    // بررسی اولیه دکمه
    triggerValidation();
}