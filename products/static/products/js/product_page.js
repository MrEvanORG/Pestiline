/**
 * Pestiline Product Detail Logic - Full Version
 * Includes: Slider (RTL), Price Calculator, Advanced Cart System
 */

let typingTimer; // تایمر برای تاخیر در ارسال درخواست وزن (Debounce)

document.addEventListener('DOMContentLoaded', () => {
    initSlider();
    initPriceCalculator();
    initCartSystem();

    // اگر محصول از قبل در سبد بود، وضعیت دکمه و اینپوت‌ها را تنظیم کن
    if (typeof PRODUCT_DATA !== 'undefined' && PRODUCT_DATA.inCart) {
        setButtonState(true);
        syncInputWithCart();
    }
});

// ============================================
// 1. Slider Logic (RTL & Touch Optimized)
// ============================================
// ============================================
// 1. Slider Logic (RTL FIXED)
// ============================================
// ============================================
// 1. Slider Logic (RTL FIXED - Final)
// ============================================
function initSlider() {
    const track = document.getElementById('sliderTrack');
    const stage = document.getElementById('galleryStage');
    const thumbs = document.querySelectorAll('.thumb-item');
    const btnNext = document.getElementById('btnNext');
    const btnPrev = document.getElementById('btnPrev');

    if (!track || !stage) return;

    let currentIndex = 0;
    const totalSlides = (typeof PRODUCT_DATA !== 'undefined')
        ? PRODUCT_DATA.imagesCount
        : 0;

    if (totalSlides <= 0) return;

    // دکمه‌ها
    if (btnNext) btnNext.onclick = () => slideTo(currentIndex + 1);
    if (btnPrev) btnPrev.onclick = () => slideTo(currentIndex - 1);

    // کلیک روی thumbnail
    thumbs.forEach(thumb => {
        thumb.addEventListener('click', () => {
            const idx = parseInt(thumb.getAttribute('data-index'));
            slideTo(idx);
        });
    });

    // ---------------- Drag Logic ----------------
    let isDragging = false;
    let startPos = 0;
    let currentTranslate = 0;
    let prevTranslate = 0;
    let animationID;

    stage.addEventListener('mousedown', touchStart);
    stage.addEventListener('touchstart', touchStart, { passive: true });
    stage.addEventListener('mouseup', touchEnd);
    stage.addEventListener('mouseleave', () => { if (isDragging) touchEnd(); });
    stage.addEventListener('touchend', touchEnd);
    stage.addEventListener('mousemove', touchMove);
    stage.addEventListener('touchmove', touchMove, { passive: true });
    stage.oncontextmenu = e => { e.preventDefault(); return false; };

    function touchStart(event) {
        isDragging = true;
        startPos = getPositionX(event);
        animationID = requestAnimationFrame(animation);
        track.style.transition = 'none';
    }

    function touchMove(event) {
        if (!isDragging) return;

        const currentPosition = getPositionX(event);
        const diff = currentPosition - startPos; // کشیدن چپ به راست = مثبت، راست به چپ = منفی

        let move = diff;

        // اصلاح مقاومت لبه‌ها برای RTL
        // اگر عکس اولیم و به سمت چپ می‌کشیم (diff < 0) -> مقاومت (جلوگیری از سفیدی)
        // اگر عکس آخریم و به سمت راست می‌کشیم (diff > 0) -> مقاومت
        if ((currentIndex === 0 && diff < 0) ||
            (currentIndex === totalSlides - 1 && diff > 0)) {
            move = diff / 3;
        }

        currentTranslate = prevTranslate + move;
    }

    function touchEnd() {
        isDragging = false;
        cancelAnimationFrame(animationID);

        const movedBy = currentTranslate - prevTranslate;
        const threshold = 60;

        // در محیط RTL:
        // اگر نوار به اندازه کافی به راست کشیده شد (movedBy > threshold)، عکس بعدی را نشان بده
        // اگر به چپ کشیده شد (movedBy < -threshold)، عکس قبلی را نشان بده
        if (movedBy > threshold && currentIndex < totalSlides - 1) {
            currentIndex += 1;
        } else if (movedBy < -threshold && currentIndex > 0) {
            currentIndex -= 1;
        }

        slideTo(currentIndex);
    }

    function getPositionX(event) {
        return event.type.includes('mouse')
            ? event.pageX
            : event.touches[0].clientX;
    }

    function animation() {
        setSliderPosition();
        if (isDragging) requestAnimationFrame(animation);
    }

    function setSliderPosition() {
        track.style.transform = `translateX(${currentTranslate}px)`;
    }

    function slideTo(index) {
        index = Math.max(0, Math.min(index, totalSlides - 1));
        currentIndex = index;

        const stageWidth = stage.offsetWidth;

        // مقدار مثبت در RTL باعث حرکت نوار به راست و نمایش عکس سمت چپ (عکس بعدی) می‌شود
        currentTranslate = currentIndex * stageWidth;
        prevTranslate = currentTranslate;

        track.style.transition = 'transform 0.4s cubic-bezier(0.25, 1, 0.5, 1)';
        setSliderPosition();
        updateThumbs();
    }

    function updateThumbs() {
        thumbs.forEach(t => t.classList.remove('active'));
        const active = thumbs[currentIndex];
        if (active) {
            active.classList.add('active');

            // جلوگیری از پرش صفحه به بالا
            const container = document.getElementById('galleryThumbs');
            if (container) {
                const scrollPos =
                    active.offsetLeft -
                    container.offsetWidth / 2 +
                    active.offsetWidth / 2;

                container.scrollTo({
                    left: scrollPos,
                    behavior: 'smooth'
                });
            }
        }
    }

    window.addEventListener('resize', () => {
        slideTo(currentIndex);
    });
}



// ============================================
// 2. Price Calculation & Input Logic
// ============================================
// ============================================
// 2. Price Calculation & Input Logic
// ============================================
function initPriceCalculator() {
    forceValidValue(); // در لود اولیه مقادیر را تنظیم و قیمت را حساب کند
}

window.updateQty = function(change) {
    const input = document.getElementById('qtyInput');
    if (!input) return;
    let newVal = parseInt(input.value) || 0;
    input.value = newVal + change;
    
    forceValidValue();  
    handleQtyChange();
};

window.setWeight = function(weight, element) {
    const input = document.getElementById('weightInput');
    if (!input) return;
    input.value = weight;
    document.querySelectorAll('.weight-tag').forEach(tag => tag.classList.remove('active'));
    if (element) element.classList.add('active');
    
    forceValidValue(); 
    handleQtyChange();
};

window.manualWeightInput = function() {
    document.querySelectorAll('.weight-tag').forEach(tag => tag.classList.remove('active'));
    
    // محاسبه پیش‌نمایش قیمت حین تایپ (بدون اصلاح اجباری اینپوت)
    calculateTempPrice(); 

    // تشخیص اتمام تایپ (۸۰۰ میلی ثانیه)
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
        forceValidValue(); // اصلاح ظاهری عدد
        handleQtyChange(); // ارسال ریکوئست به بک‌اند در صورت موجود بودن در سبد
    }, 800);
};

// محاسبه قیمت حین تایپ (بدون تغییر دادن عدد داخل اینپوت)
function calculateTempPrice() {
    const priceDisplay = document.getElementById('finalPriceDisplay');
    const el = PRODUCT_DATA.isPackaged ? document.getElementById('qtyInput') : document.getElementById('weightInput');
    if (!priceDisplay || !el) return;

    let val = parseFloat(el.value);
    if (isNaN(val) || val <= 0) val = 0; // فقط برای نمایش موقت مبلغ صفر شود
    
    const total = val * PRODUCT_DATA.price;
    priceDisplay.textContent = `${Math.round(total).toLocaleString('en-US')} تومان`;
}

// تابع اصلی برای بررسی Min/Max و تصحیح مقدار ظاهری و نهایی کردن قیمت
function forceValidValue() {
    const priceDisplay = document.getElementById('finalPriceDisplay');
    const el = PRODUCT_DATA.isPackaged ? document.getElementById('qtyInput') : document.getElementById('weightInput');
    if (!priceDisplay || !el) return;

    const minOrder = PRODUCT_DATA.minOrder;
    const maxOrder = PRODUCT_DATA.maxOrder;

    let val = parseFloat(el.value);
    
    // اعمال قوانین Min و Max
    if (isNaN(val) || val < minOrder) val = minOrder;
    if (val > maxOrder) val = maxOrder;
    
    // اگر بسته ای است، باید عدد صحیح باشد
    if (PRODUCT_DATA.isPackaged) val = Math.round(val);

    // آپدیت ظاهری اینپوت به مقدار تصحیح شده
    if (el.value !== String(val)) {
        el.value = val;
    }

    // محاسبه قیمت نهایی
    const total = val * PRODUCT_DATA.price;
    priceDisplay.textContent = `${Math.round(total).toLocaleString('en-US')} تومان`;
}




// ============================================
// 3. Advanced Cart System
// ============================================
function initCartSystem() {
    const btn = document.querySelector('.btn-pro-cart');
    if (btn) btn.addEventListener('click', handleMainBtnClick);
    
    // رویداد input برای weightInput قبلا در manualWeightInput هندل شد،
    // پس نیازی نیست اینجا دوباره eventListener برای تایمر بگذارید.
}

function syncInputWithCart() {
    if (!PRODUCT_DATA.currentQty || PRODUCT_DATA.currentQty <= 0) return;

    if (PRODUCT_DATA.isPackaged) {
        const qtyEl = document.getElementById('qtyInput');
        if (qtyEl) {
            qtyEl.value = parseInt(PRODUCT_DATA.currentQty);
            forceValidValue();
        }
    } else {
        const weightEl = document.getElementById('weightInput');
        if (weightEl) {
            weightEl.value = parseFloat(PRODUCT_DATA.currentQty);
            document.querySelectorAll('.weight-tag').forEach(tag => {
                const val = parseFloat(tag.getAttribute('onclick').match(/[\d.]+/)[0]);
                if (val === parseFloat(PRODUCT_DATA.currentQty)) {
                    tag.classList.add('active');
                } else {
                    tag.classList.remove('active');
                }
            });
            forceValidValue();
        }
    }
}

function handleMainBtnClick(e) {
    const btn = e.currentTarget;
    if (btn.hasAttribute('disabled')) return;

    const isRemoving = btn.classList.contains('added');
    const action = isRemoving ? 'remove' : 'add';
    sendCartRequest(action);
}

function handleQtyChange() {
    const btn = document.querySelector('.btn-pro-cart');
    if (btn && btn.classList.contains('added')) {
        sendCartRequest('update');
    }
}

function sendCartRequest(action) {
    const btn = document.querySelector('.btn-pro-cart');
    if (!btn) return;

    let quantity = 0;
    if (PRODUCT_DATA.isPackaged) {
        quantity = parseInt(document.getElementById('qtyInput').value);
    } else {
        quantity = parseFloat(document.getElementById('weightInput').value);
    }

    let msgType = '';
    if (action === 'update') {
        if (quantity > PRODUCT_DATA.currentQty) msgType = 'increased';
        else if (quantity < PRODUCT_DATA.currentQty) msgType = 'decreased';
        else return;
    }

    btn.setAttribute('disabled', 'disabled');
    btn.style.opacity = '0.8';

    fetch('/api/cart/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            product_id: PRODUCT_DATA.id,
            action: action,
            quantity: quantity
        })
    })
    .then(resp => resp.json())
    .then(data => {
        btn.removeAttribute('disabled');
        btn.style.opacity = '1';
        if (data.success) {
            setButtonState(data.in_cart);
            updateHeaderBadge(data.cart_count);
            PRODUCT_DATA.currentQty = quantity;
            if (action === 'update' && data.in_cart) {
                showTempMessage(msgType);
            }
        } else {
            alert('خطا: ' + data.message);
        }
    })
    .catch(err => {
        console.error(err);
        btn.removeAttribute('disabled');
        btn.style.opacity = '1';
    });
}

function showTempMessage(type) {
    const btn = document.querySelector('.btn-pro-cart');
    const textSpan = btn.querySelector('.btn-text');
    const icon = btn.querySelector('.btn-right i');

    let msg = type === 'increased' ? 'تعداد افزایش یافت' : 'تعداد کاهش یافت';
    if (!PRODUCT_DATA.isPackaged) {
        msg = type === 'increased' ? 'وزن افزایش یافت' : 'وزن کاهش یافت';
    }

    const prevText = textSpan.textContent;
    const prevIcon = icon.className;

    textSpan.textContent = msg;
    icon.className = 'fa-slab-press fa-regular fa-check-double';
    btn.classList.add('updated-anim');

    setTimeout(() => {
        if (btn.classList.contains('added')) {
            textSpan.textContent = 'در سبد خرید (حذف؟)';
            icon.className = 'fa-slab-press fa-regular fa-trash';
        }
        btn.classList.remove('updated-anim');
    }, 2000);
}

function setButtonState(isInCart) {
    const btn = document.querySelector('.btn-pro-cart');
    const icon = btn.querySelector('.btn-right i');
    const text = btn.querySelector('.btn-text');
    const completeCartEl = document.getElementById('completeCart');

    // نمایش یا مخفی کردن لینک تکمیل سبد خرید
    if (completeCartEl) {
        completeCartEl.style.display = isInCart ? 'block' : 'none';
    }

    if (isInCart) {
        btn.classList.add('added');
        icon.className = 'fa-slab-press fa-regular fa-trash';
        text.textContent = 'در سبد خرید (حذف؟)';
        btn.classList.add('animating');
        setTimeout(() => btn.classList.remove('animating'), 600);
    } else {
        btn.classList.remove('added');
        icon.className = 'fa-slab-press fa-regular fa-bag-shopping';
        text.textContent = 'افزودن به سبد';
    }
}

function updateHeaderBadge(count) {
    const badge = document.getElementById('cartBadge');
    if (!badge) return;
    badge.textContent = count;
    if (count > 0) {
        badge.style.display = 'flex';
        badge.classList.remove('pop');
        void badge.offsetWidth;
        badge.classList.add('pop');
    } else {
        badge.style.display = 'none';
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let c of cookies) {
            c = c.trim();
            if (c.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
