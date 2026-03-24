/**
 * Pestiline Checkout Form Validation & Logic
 * Features: Smart Pop-up, Live Validation, Data Persistence Check
 */

document.addEventListener('DOMContentLoaded', () => {
    setupCheckoutLogic();
});

function setupCheckoutLogic() {
    const selfReceiverCheckbox = document.getElementById('selfReceiver');
    const btnSubmit = document.getElementById('btnSubmitOrder');
    const inputs = document.querySelectorAll('#checkoutForm input[data-validate], #checkoutForm textarea[data-validate]');

    // ۱. مدیریت تیک "گیرنده خودم هستم"
    if (selfReceiverCheckbox) {
        selfReceiverCheckbox.addEventListener('change', toggleReceiverInputs);
    }

    // ۲. متصل کردن رویدادها به اینپوت‌ها برای اعتبارسنجی زنده (Live)
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            if (input.classList.contains('touched')) {
                updateUI(input);
            }
            triggerValidation();
        });

        input.addEventListener('blur', () => {
            input.classList.add('touched');
            updateUI(input);
            triggerValidation();
        });
    });

    // ۳. مدیریت کلیک روی دکمه ثبت نهایی (منطق هوشمند پاپ‌آپ)
    if (btnSubmit) {
        btnSubmit.addEventListener('click', () => {
            // نمایش ارور همه فیلدها در صورت کلیک
            inputs.forEach(input => {
                input.classList.add('touched');
                updateUI(input);
            });

            if (checkFormValidity(inputs)) {
                // دریافت مقادیر فعلی وارد شده در فرم
                const currentAddress = document.getElementById('recAddress').value.trim();
                const currentPostal = document.getElementById('recPostal').value.trim();
                
                // بررسی اینکه آیا کاربر از قبل دیتایی داشته یا نه (خواندن از متغیر گلوبال ارسال شده از قالب)
                const hasSavedInfo = (USER_DATA.savedAddress !== "" || USER_DATA.savedPostal !== "");
                
                // بررسی اینکه آیا دیتای وارد شده با دیتای قبلی فرق دارد یا نه
                const isChanged = (currentAddress !== USER_DATA.savedAddress || currentPostal !== USER_DATA.savedPostal);

                if (!hasSavedInfo) {
                    // حالت ۱: کاربر قبلاً آدرسی نداشته، پیشنهاد ذخیره می‌دهیم
                    document.getElementById('modalSaveTitle').textContent = 'ذخیره اطلاعات ارسال؟';
                    document.getElementById('modalSaveText').textContent = 'آیا مایلید این آدرس و کد پستی برای سفارش‌های بعدی در پروفایل شما ذخیره شود تا نیازی به وارد کردن مجدد نداشته باشید؟';
                    document.getElementById('modalSaveBtn').textContent = 'بله، ذخیره کن';
                    document.getElementById('saveInfoModal').classList.add('show');
                
                } else if (isChanged) {
                    // حالت ۲: کاربر آدرس داشته اما الان تغییرش داده، پیشنهاد بروزرسانی می‌دهیم
                    document.getElementById('modalSaveTitle').textContent = 'بروزرسانی آدرس؟';
                    document.getElementById('modalSaveText').textContent = 'به نظر می‌رسد آدرس یا کد پستی خود را تغییر داده‌اید. آیا مایلید اطلاعات جدید در پروفایلتان جایگزین آدرس قبلی شود؟';
                    document.getElementById('modalSaveBtn').textContent = 'بله، بروزرسانی کن';
                    document.getElementById('saveInfoModal').classList.add('show');
                
                } else {
                    // حالت ۳: کاربر آدرس داشته و هیچ تغییری هم نداده، پاپ‌آپ باز نمی‌شود و مستقیم ثبت می‌شود
                    submitForm(false);
                }
            }
        });
    }

    // چک کردن وضعیت دکمه در زمان لود اولیه صفحه
    triggerValidation();
}

// تغییر وضعیت فیلدهای گیرنده بر اساس تیک "گیرنده خودم هستم"
function toggleReceiverInputs() {
    const isSelf = document.getElementById('selfReceiver').checked;
    const recName = document.getElementById('recName');
    const recPhone = document.getElementById('recPhone');
    
    if (isSelf) {
        recName.value = USER_DATA.fullName;
        recPhone.value = USER_DATA.phone;
        
        // قفل کردن و اعمال استایل غیرفعال
        recName.setAttribute('readonly', 'true');
        recPhone.setAttribute('readonly', 'true');
        recName.classList.add('disabled-input');
        recPhone.classList.add('disabled-input');
        
        // پاک کردن ارورها
        recName.classList.remove('invalid', 'touched');
        recPhone.classList.remove('invalid', 'touched');
        document.getElementById('error-recName').classList.remove('show');
        document.getElementById('error-recPhone').classList.remove('show');
    } else {
        recName.value = "";
        recPhone.value = "";
        
        // باز کردن قفل
        recName.removeAttribute('readonly');
        recPhone.removeAttribute('readonly');
        recName.classList.remove('disabled-input');
        recPhone.classList.remove('disabled-input');
        
        // فوکوس روی فیلد نام
        recName.focus();
    }
    triggerValidation();
}

// بررسی کلی وضعیت فرم و غیرفعال/فعال کردن دکمه اصلی
function triggerValidation() {
    const btn = document.getElementById('btnSubmitOrder');
    const inputs = document.querySelectorAll('#checkoutForm input[data-validate], #checkoutForm textarea[data-validate]');
    
    const isValid = checkFormValidity(inputs);

    if (isValid) {
        btn.removeAttribute('disabled');
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
    } else {
        btn.setAttribute('disabled', 'true');
        btn.style.cursor = 'not-allowed';
    }
}

// چک کردن اینکه آیا کل فرم معتبر است یا خیر
function checkFormValidity(inputs = document.querySelectorAll('#checkoutForm input[data-validate], #checkoutForm textarea[data-validate]')) {
    for (let input of inputs) {
        // فیلدهای readonly (مثل وقتی که تیک گیرنده خودم هستم خورده) نیازی به چک شدن ندارند
        if (!input.hasAttribute('readonly') && getErrorMsg(input) !== "") {
            return false;
        }
    }
    return true;
}

// منطق تولید متن ارور (همان امضای auth.js)
function getErrorMsg(input) {
    let val = input.value.trim();
    const type = input.dataset.validate;
    
    if (!val) return "لطفاً این فیلد را تکمیل کنید.";

    // تبدیل اعداد فارسی به انگلیسی برای چک کردن Regex
    const persianNumbers = [/۰/g, /۱/g, /۲/g, /۳/g, /۴/g, /۵/g, /۶/g, /۷/g, /۸/g, /۹/g];
    const englishNumbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
    for (let i = 0; i < 10; i++) { val = val.replace(persianNumbers[i], englishNumbers[i]); }

    const farsiOnly = /^[\u0600-\u06FF\s]+$/;
    const phonePat = /^(09)\d{9}$/;
    const postalPat = /^\d{10}$/;

    switch (type) {
        case 'name':
            if (!farsiOnly.test(val)) return "فقط حروف فارسی مجاز است.";
            if (val.length < 3) return "حداقل ۳ حرف وارد کنید.";
            break;
        case 'phone':
            if (!phonePat.test(val)) return "شماره نامعتبر است (مثال: 0912).";
            break;
        case 'address':
            if (val.length < 10) return "آدرس بسیار کوتاه است.";
            break;
        case 'postal':
            if (!postalPat.test(val)) return "کد پستی باید دقیقاً ۱۰ رقم باشد.";
            break;
    }
    return "";
}

// تغییر ظاهر فیلدها و ارورها (همان امضای auth.js)
function updateUI(input) {
    if (input.hasAttribute('readonly')) return;

    const msg = getErrorMsg(input);
    const id = input.id;
    const errEl = document.getElementById('error-' + id);

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

// ارسال نهایی فرم (از داخل پاپ‌آپ یا مستقیماً)
window.submitForm = function(shouldSave) {
    document.getElementById('saveInfoInput').value = shouldSave ? 'true' : 'false';
    document.getElementById('saveInfoModal').classList.remove('show');
    document.getElementById('checkoutForm').submit();
}