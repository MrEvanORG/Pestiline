/**
 * Pestiline Authentication System - Final Fixed Version
 * Features: 
 * 1. Data Persistence on 'Back' button (City/Province)
 * 2. Active Tab Retention
 * 3. Smart Validation
 */

// متغیر گلوبال برای دسترسی به تابع لود شهر در scope اصلی
let loadCitiesForProvince;

document.addEventListener('DOMContentLoaded', () => {
    setupCustomDropdowns();
    setupFormLogic();
    setupTabsAndUI();

    // ============================================================
    // اصلاح حیاتی: بازخوانی شهرها اگر کاربر از دکمه Back استفاده کرده باشد
    // ============================================================
    const preSelectedProvinceId = document.getElementById('province-hidden').value;
    if (preSelectedProvinceId && typeof loadCitiesForProvince === 'function') {
        // false یعنی: لیست شهرها را بیار، اما متنی که جنگو در اینپوت شهر نوشته را پاک نکن!
        loadCitiesForProvince(preSelectedProvinceId, false);
    }
});

// ==========================================
// 1. سیستم دراپ‌دان‌های سفارشی (استان و شهر)
// ==========================================
function setupCustomDropdowns() {
    const provSearch = document.getElementById('province-search');
    const provHidden = document.getElementById('province-hidden');
    const provList = document.getElementById('province-list');
    const provWrapper = provSearch.closest('.dropdown-wrapper');

    const citySearch = document.getElementById('city-search');
    const cityHidden = document.getElementById('city-hidden');
    const cityList = document.getElementById('city-list');
    const cityWrapper = citySearch.closest('.dropdown-wrapper');
    const cityGroup = document.getElementById('city-dropdown-group');

    let allProvinces = [];
    let currentCities = [];

    // لود اولیه استان‌ها
    fetch('/api/provinces/')
        .then(res => res.json())
        .then(data => { allProvinces = data; })
        .catch(console.error);

    // توابع کمکی
    function toggleDropdown(wrapper, show) {
        if (show) wrapper.classList.add('open');
        else setTimeout(() => wrapper.classList.remove('open'), 200);
    }

    function renderList(ul, items, searchInp, hiddenInp, type) {
        ul.innerHTML = '';
        if (items.length === 0) {
            ul.innerHTML = '<li class="no-result">نتیجه‌ای یافت نشد</li>';
            return;
        }
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.name;
            li.addEventListener('click', () => {
                searchInp.value = item.name;
                hiddenInp.value = item.id;
                
                triggerValidation();

                if (type === 'province') {
                    // وقتی کاربر دستی کلیک می‌کند، باید شهر قبلی پاک شود (true)
                    loadCitiesForProvince(item.id, true);
                }
            });
            ul.appendChild(li);
        });
    }

    // تعریف تابع لود شهر (که حالا به متغیر گلوبال وصل می‌شود)
    loadCitiesForProvince = function(provId, shouldResetCity = true) {
        // فعال کردن بخش شهر
        cityGroup.classList.remove('disabled');
        citySearch.removeAttribute('disabled');
        
        // اگر کاربر دستی استان را عوض کرده، شهر را ریست کن
        // اما اگر صفحه تازه لود شده (Back زده)، به مقدار جنگو دست نزن
        if (shouldResetCity) {
            citySearch.value = '';
            citySearch.placeholder = "در حال بارگذاری...";
            cityHidden.value = '';
        }

        fetch(`/api/cities/?province_id=${provId}`)
            .then(res => res.json())
            .then(data => {
                currentCities = data;
                if (shouldResetCity) {
                    citySearch.placeholder = "شهر خود را انتخاب کنید...";
                }
                // لیست را رندر کن تا آماده کلیک باشد
                renderList(cityList, currentCities, citySearch, cityHidden, 'city');
            })
            .catch(() => {
                citySearch.placeholder = "خطا در ارتباط";
            });
    };

    // رویدادهای استان
    provSearch.addEventListener('focus', () => {
        provSearch.value = ''; 
        renderList(provList, allProvinces, provSearch, provHidden, 'province');
        toggleDropdown(provWrapper, true);
    });
    provSearch.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = allProvinces.filter(p => p.name.includes(term));
        renderList(provList, filtered, provSearch, provHidden, 'province');
        toggleDropdown(provWrapper, true);
        provHidden.value = ''; 
        triggerValidation();
    });
    provSearch.addEventListener('blur', () => toggleDropdown(provWrapper, false));

    // رویدادهای شهر
    citySearch.addEventListener('focus', () => {
        citySearch.value = '';
        renderList(cityList, currentCities, citySearch, cityHidden, 'city');
        toggleDropdown(cityWrapper, true);
    });
    citySearch.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = currentCities.filter(c => c.name.includes(term));
        renderList(cityList, filtered, citySearch, cityHidden, 'city');
        toggleDropdown(cityWrapper, true);
        cityHidden.value = '';
        triggerValidation();
    });
    citySearch.addEventListener('blur', () => toggleDropdown(cityWrapper, false));
}

// ==========================================
// 2. منطق اعتبارسنجی (Validation Logic)
// ==========================================

function setupFormLogic() {
    const inputs = document.querySelectorAll('#register-form input[data-validate]');
    
    inputs.forEach(input => {
        // آپدیت وضعیت دکمه هنگام تایپ
        input.addEventListener('input', () => {
            triggerValidation();
            // اگر فیلد قبلا قرمز شده، با تایپ کردن وضعیتش را آپدیت کن
            if (input.classList.contains('touched')) {
                updateUI(input);
            }
        });

        // نمایش ارور هنگام خروج از فیلد
        input.addEventListener('blur', () => {
            input.classList.add('touched');
            updateUI(input);
            triggerValidation();
        });
    });

    // سابمیت ثبت‌نام
    document.getElementById('register-form').addEventListener('submit', (e) => {
        if (!checkFormValidity()) e.preventDefault();
    });

    // سابمیت لاگین
    document.getElementById('login-form').addEventListener('submit', (e) => {
        const ph = document.getElementById('login-phone').value;
        const ps = document.getElementById('login-pass').value;
        if(!ph || !ps) {
            e.preventDefault();
            const err = document.getElementById('login-general-error');
            err.textContent = "لطفاً اطلاعات را کامل وارد کنید.";
            err.classList.add('show');
        }
    });
}

function triggerValidation() {
    const btn = document.querySelector('#register-form .btn-auth');
    const isValid = checkFormValidity();

    if (isValid) {
        btn.removeAttribute('disabled');
        btn.style.cursor = 'pointer';
        // متن دکمه می‌تواند ثابت بماند یا تغییر کند
    } else {
        btn.setAttribute('disabled', 'true');
        btn.style.cursor = 'not-allowed';
    }
}

function checkFormValidity() {
    const isOtpMode = document.getElementById('otp-only-check').checked;
    
    // 1. فیلدهای متنی
    const inputs = document.querySelectorAll('#register-form input[data-validate="name"], #register-form input[data-validate="phone"]');
    for (let input of inputs) {
        if (getErrorMsg(input) !== "") return false;
    }

    // 2. استان
    const pVal = document.getElementById('province-hidden').value;
    if (!pVal) return false;

    // 3. شهر (اگر فعال باشد)
    const cVal = document.getElementById('city-hidden').value;
    const isCityDisabled = document.getElementById('city-dropdown-group').classList.contains('disabled');
    if (!isCityDisabled && !cVal) return false;

    // 4. پسورد (اگر OTP نباشد)
    if (!isOtpMode) {
        const passInput = document.getElementById('reg-pass');
        const confirmInput = document.getElementById('reg-confirm');
        
        if (getErrorMsg(passInput) !== "") return false;
        if (getErrorMsg(confirmInput) !== "") return false;

        // چک نهایی خالی نبودن
        if (!passInput.value || !confirmInput.value) return false;
    }

    return true;
}

function getErrorMsg(input) {
    const val = input.value.trim();
    const type = input.dataset.validate;
    const isOtpMode = document.getElementById('otp-only-check').checked;

    if (isOtpMode && (type === 'password' || type === 'confirm')) return "";

    if (!val) return "لطفاً تکمیل کنید.";

    const farsiOnly = /^[\u0600-\u06FF\s]+$/;
    const phonePat = /^(09|۰۹)[0-9۰-۹]{9}$/;
    const strictPass = /^(?=.*[a-zA-Z])(?=.*[0-9!@#$%^&*])[a-zA-Z0-9!@#$%^&*]{6,}$/;

    switch (type) {
        case 'name':
            if (!farsiOnly.test(val)) return "فقط حروف فارسی";
            if (val.length < 3) return "حداقل ۳ حرف";
            break;

        case 'phone':
            if (!phonePat.test(val)) return "شماره نامعتبر است";
            break;

        case 'password':
            if (!strictPass.test(val)) return "حداقل ۶ کاراکتر (انگلیسی + عدد/نماد)";
            break;

        case 'confirm':
            const originalPass = document.getElementById('reg-pass').value;
            if (val !== originalPass) return "رمز عبور یکسان نیست";
            break;
    }

    return "";
}

function updateUI(input) {
    const msg = getErrorMsg(input);
    const id = input.id;
    const errEl = document.getElementById('error-' + id);
    const inpEl = document.getElementById(id);
    const noteEl = document.getElementById('note-' + id);

    // مدیریت نوت زیر موبایل
    if (input.dataset.validate === 'phone') {
        if (msg === "") {
            if(noteEl) noteEl.style.display = 'block';
            if(errEl) errEl.classList.remove('show');
            if(inpEl) inpEl.classList.remove('invalid');
            return;
        } else {
            if(noteEl) noteEl.style.display = 'none';
        }
    }

    if (errEl) {
        errEl.textContent = msg;
        if (msg !== "") {
            errEl.classList.add('show');
            if (inpEl) inpEl.classList.add('invalid');
        } else {
            errEl.classList.remove('show');
            if (inpEl) inpEl.classList.remove('invalid');
        }
    }
}

// ==========================================
// 3. تنظیمات UI عمومی (OTP و تب‌ها)
// ==========================================
function setupTabsAndUI() {
    window.showTab = (type) => {
        document.querySelectorAll('.auth-form, .tab-btn').forEach(el => el.classList.remove('active'));
        document.getElementById(type + '-form').classList.add('active');
        const btns = document.querySelectorAll('.tab-btn');
        btns.forEach(b => {
            if(b.getAttribute('onclick').includes(type)) b.classList.add('active');
        });
    }

    window.togglePassword = (id, icon) => {
        const inp = document.getElementById(id);
        const isP = inp.type === "password";
        inp.type = isP ? "text" : "password";
        icon.classList.replace(isP ? "fa-eye-slash" : "fa-eye", isP ? "fa-eye" : "fa-eye-slash");
    }

    const otpCheck = document.getElementById('otp-only-check');
    if (otpCheck) {
        otpCheck.addEventListener('change', function() {
            const sec = document.getElementById('password-section');
            const inps = sec.querySelectorAll('input');
            
            if (this.checked) {
                sec.classList.add('hidden-mode');
                inps.forEach(i => {
                    i.value = ''; 
                    i.classList.remove('invalid', 'touched');
                    // حذف ارورهای نمایشی
                    const errPass = document.getElementById('error-reg-pass');
                    const errConf = document.getElementById('error-reg-confirm');
                    if(errPass) errPass.classList.remove('show');
                    if(errConf) errConf.classList.remove('show');
                });
            } else {
                sec.classList.remove('hidden-mode');
            }
            triggerValidation();
        });

        // چک کردن وضعیت اولیه (برای وقتی که کاربر Back زده و تیک قبلا خورده بوده)
        if (otpCheck.checked) {
            document.getElementById('password-section').classList.add('hidden-mode');
        }
    }

    // باز کردن تب فعال بر اساس دستور جنگو
    if (typeof ACTIVE_TAB !== 'undefined' && ACTIVE_TAB) {
        showTab(ACTIVE_TAB);
    }
    
    // بررسی وضعیت دکمه در لحظه لود (برای وقتی اطلاعات پر است)
    triggerValidation();
}
// ==========================================
// 4. مدیریت درخواست‌های ورود با OTP و فراموشی رمز
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    const otpLink = document.querySelector('.otp-link');
    const forgotLink = document.querySelector('.forgot-link');
    
    function handleSpecialLoginRequest(e, intent) {
        e.preventDefault();
        
        const phoneInput = document.getElementById('login-phone');
        const errEl = document.getElementById('error-login-phone');
        const genErrEl = document.getElementById('login-general-error');
        
        let val = phoneInput.value.trim();
        
        // تبدیل اعداد فارسی به انگلیسی
        const persianNumbers = [/۰/g, /۱/g, /۲/g, /۳/g, /۴/g, /۵/g, /۶/g, /۷/g, /۸/g, /۹/g];
        const englishNumbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
        for (let i = 0; i < 10; i++) { val = val.replace(persianNumbers[i], englishNumbers[i]); }
        
        // ۱. بررسی خالی بودن فیلد
        if(!val) {
            errEl.textContent = intent === 'login' ? "برای ورود با کد لطفاً شماره تلفن خود را وارد نمایید." : "برای بازیابی رمز، لطفاً شماره تلفن خود را وارد نمایید.";
            errEl.classList.add('show');
            phoneInput.classList.add('invalid');
            phoneInput.focus();
            return;
        }
        
        // ۲. بررسی فرمت صحیح شماره
        if(!/^(09|۰۹)[0-9۰-۹]{9}$/.test(val)) {
            errEl.textContent = "شماره نامعتبر است (مثال: 0912).";
            errEl.classList.add('show');
            phoneInput.classList.add('invalid');
            return;
        }
        
        errEl.classList.remove('show');
        phoneInput.classList.remove('invalid');
        genErrEl.classList.remove('show');
        
        // ۳. حالت Loading دکمه
        const originalText = e.target.innerHTML;
        e.target.innerHTML = '<i class="fa-duotone fa-spinner-third fa-spin"></i> لطفا صبر کنید...';
        e.target.style.pointerEvents = 'none';
        e.target.style.opacity = '0.7';
        
        // ۴. ارسال درخواست به سرور
        fetch('/api/auth/request-otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ phone_number: val, intent: intent })
        })
        .then(res => res.json())
        .then(data => {
            if(data.success || data.rate_limited) {
                // هدایت به صفحه تایید کد
                window.location.href = '/auth/verify/';
            } else {
                // نمایش ارور از سمت سرور (مثلا کاربر یافت نشد)
                genErrEl.textContent = data.message;
                genErrEl.classList.add('show');
                resetLinkBtn();
            }
        })
        .catch(err => {
            genErrEl.textContent = "خطا در ارتباط با سرور، لطفاً اینترنت را بررسی کنید.";
            genErrEl.classList.add('show');
            resetLinkBtn();
        });

        function resetLinkBtn() {
            e.target.innerHTML = originalText;
            e.target.style.pointerEvents = 'auto';
            e.target.style.opacity = '1';
        }
    }
    
    // اتصال رویدادها
    if(otpLink) otpLink.addEventListener('click', (e) => handleSpecialLoginRequest(e, 'login'));
    if(forgotLink) forgotLink.addEventListener('click', (e) => handleSpecialLoginRequest(e, 'reset_password'));
});

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