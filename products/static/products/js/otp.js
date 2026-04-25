/**
 * Pestiline OTP Logic - Final Production Version
 * Connected to Django Backend
 */

document.addEventListener('DOMContentLoaded', () => {
    setupOTP();
    setupTimer(); 
});

// ==========================================
// 1. مدیریت ورودی‌های OTP (Ghost Input)
// ==========================================
function setupOTP() {
    const realInput = document.getElementById('otp-real-input');
    const displayBoxes = document.querySelectorAll('.otp-box');
    const form = document.getElementById('otp-form');

    // فوکوس اولیه خودکار
    setTimeout(() => realInput.focus(), 100);

    // مدیریت تایپ و آپدیت ویژوال‌ها
    realInput.addEventListener('input', (e) => {
        // فقط اعداد مجاز هستند
        const val = e.target.value.replace(/[^0-9]/g, '');
        e.target.value = val;

        // پاک کردن ارورها هنگام تایپ
        document.querySelector('.otp-wrapper').classList.remove('error');
        document.getElementById('otp-error').classList.remove('show');

        // آپدیت باکس‌ها
        updateBoxes(val);

        // اگر 6 رقم پر شد، خودکار سابمیت شود
        if (val.length === 6) {
            verifyCode(val);
        }
    });

    // تابع آپدیت گرافیک باکس‌ها
    function updateBoxes(value) {
        displayBoxes.forEach((box, index) => {
            box.className = 'otp-box';
            
            if (index < value.length) {
                box.textContent = value[index];
                box.classList.add('filled');
            } else {
                box.textContent = '';
                if (index === value.length) {
                    box.classList.add('active');
                }
            }
        });
    }

    // هندل کردن سابمیت دستی (اینتر یا دکمه)
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const code = realInput.value;
        if (code.length < 6) {
            showError("لطفاً کد ۶ رقمی را کامل وارد کنید.");
        } else {
            verifyCode(code);
        }
    });
}

// ==========================================
// 2. توابع ارتباط با سرور (AJAX)
// ==========================================

function verifyCode(code) {
    const btn = document.getElementById('verify-btn');
    const wrapper = document.querySelector('.otp-wrapper');
    const realInput = document.getElementById('otp-real-input');
    const originalText = '<i class="fa-regular fa-check"></i> تایید و ورود'; // متن اصلی دکمه را ذخیره نمی‌کنیم تا آیکون نپرد

    // حالت لودینگ
    btn.innerHTML = '<i class="fa-duotone fa-spinner-third fa-spin"></i> در حال بررسی...';
    btn.disabled = true;
    realInput.disabled = true;

    // ارسال درخواست واقعی به جنگو
    fetch('/api/auth/verify_code/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ code: code })
    })
    .then(async response => {
        const data = await response.json();
        
        if (response.ok && data.success) {
            // موفقیت
            btn.innerHTML = '<i class="fa-regular fa-check"></i> تایید شد';
            btn.style.background = "var(--secondary)";
            window.location.href = data.redirect_url;
        } else {
            // خطا (کد اشتباه یا منقضی)
            throw new Error(data.message || 'خطایی رخ داده است.');
        }
    })
    .catch(error => {
        let msg = error.message;
        if (msg === 'Failed to fetch') msg = 'اتصال اینترنت شما برقرار نیست.';
        
        showError(msg);
        
        // بازگشت به حالت عادی
        btn.innerHTML = originalText; // متن پیش‌فرض دکمه
        btn.disabled = false;
        realInput.disabled = false;
        realInput.value = ''; // پاک کردن کد
        realInput.focus();
        
        wrapper.classList.add('error');
        // ریست کردن باکس‌های گرافیکی
        document.querySelectorAll('.otp-box').forEach(b => {
            b.textContent = '';
            b.className = 'otp-box';
        });
        document.querySelector('.otp-box').classList.add('active');
    });
}

// ==========================================
// 3. منطق تایمر و ارسال مجدد
// ==========================================

function setupTimer() {
    const timerText = document.getElementById('timer-text');
    const display = document.getElementById('countdown');
    const resendBtn = document.getElementById('resend-btn');
    
    // دریافت زمان باقی‌مانده از متغیر گلوبال (که از تمپلیت آمده)
    let remainingTime = (typeof SERVER_TIMER_REMAINING !== 'undefined') ? SERVER_TIMER_REMAINING : 0;

    function startCountdown(duration) {
        // محاسبه زمان پایان بر اساس زمان حال کلاینت
        const now = Math.floor(Date.now() / 1000);
        const endTime = now + duration;

        runInterval(endTime);
    }

    function runInterval(endTime) {
        // تنظیم وضعیت اولیه UI
        timerText.style.display = 'block';
        resendBtn.style.display = 'none';

        const int = setInterval(() => {
            const now = Math.floor(Date.now() / 1000);
            const left = endTime - now;

            if (left <= 0) {
                clearInterval(int);
                showResendButton();
            } else {
                const m = Math.floor(left / 60).toString().padStart(2, '0');
                const s = (left % 60).toString().padStart(2, '0');
                if(display) display.textContent = `${m}:${s}`;
            }
        }, 1000);
    }

    function showResendButton() {
        timerText.style.display = 'none';
        resendBtn.style.display = 'flex';
        resendBtn.disabled = false;
    }

    // هندل کردن دکمه ارسال مجدد
    resendBtn.addEventListener('click', () => {
        resendBtn.disabled = true;
        resendBtn.innerHTML = '<i class="fa-duotone fa-spinner-third fa-spin"></i> در حال ارسال...';

        fetch('/api/auth/resend-code/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(async response => {
            const data = await response.json();
            if (response.ok && data.success) {
                // موفقیت: ریست کردن تایمر با زمان جدید (ttl)
                resendBtn.innerHTML = '<i class="fa-regular fa-rotate-right"></i> ارسال مجدد کد';
                startCountdown(data.ttl);
                
                showError("کد جدید با موفقیت ارسال شد.", true); 
            } else {
                throw new Error(data.message || 'خطا در ارسال مجدد.');
            }
        })
        .catch(error => {
            resendBtn.disabled = false;
            resendBtn.innerHTML = '<i class="fa-regular fa-rotate-right"></i> ارسال مجدد کد';
            let msg = error.message;
            if (msg === 'Failed to fetch') msg = 'اتصال اینترنت شما برقرار نیست.';
            showError(msg);
        });
    });

    // بررسی وضعیت اولیه در لحظه لود صفحه
    if (remainingTime > 0) {
        startCountdown(remainingTime);
    } else {
        showResendButton();
    }
}

// تابع نمایش پیام خطا (یا موفقیت)
function showError(msg, isSuccess=false) {
    const errorEl = document.getElementById('otp-error');
    errorEl.textContent = msg;
    errorEl.classList.add('show');
    
    if (isSuccess) {
        errorEl.style.color = 'var(--secondary)'; // سبز
        // پیام موفقیت بعد از ۳ ثانیه محو شود
        setTimeout(() => { 
            errorEl.classList.remove('show'); 
            errorEl.style.color = ''; 
        }, 3000);
    } else {
        errorEl.style.color = '#ff4d4d'; // قرمز
        // لرزش باکس‌ها فقط در حالت خطا
        document.querySelector('.otp-wrapper').classList.add('error');
        setTimeout(() => document.querySelector('.otp-wrapper').classList.remove('error'), 500);
    }
}

// تابع دریافت کوکی CSRF برای جنگو
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}