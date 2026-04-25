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

    // تنظیمات درگ
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
        const currentMove = currentPosition - startPos;
        let moveWithResistance = currentMove;
        // مقاومت در لبۀ اسلایدر
        if ((currentIndex === 0 && currentMove > 0) ||
            (currentIndex === totalSlides - 1 && currentMove < 0)) {
            moveWithResistance = currentMove / 3;
        }
        currentTranslate = prevTranslate + moveWithResistance;
    }

    function touchEnd() {
        isDragging = false;
        cancelAnimationFrame(animationID);
        const movedBy = currentTranslate - prevTranslate;
        const threshold = 50;

        if (movedBy < -threshold && currentIndex < totalSlides - 1) {
            currentIndex -= 1;//gam
        } else if (movedBy > threshold && currentIndex > 0) {
            currentIndex += 1;//gam
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
        // محدود کردن ایندکس
        index = Math.max(0, Math.min(index, totalSlides - 1));
        currentIndex = index;
        const stageWidth = stage.offsetWidth;
        // برای RTL: منفی می‌کنیم تا جهت سوایپ اصلاح شود
        currentTranslate = currentIndex * stageWidth;//gam
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
            active.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            });
        }
    }

    window.addEventListener('resize', () => {
        track.style.transition = 'none';
        slideTo(currentIndex);
    });
}

// ============================================
// 2. Price Calculation & Input Logic
// ============================================
function initPriceCalculator() {
    updateFinalPrice();
}

const originalUpdateQty = window.updateQty;
window.updateQty = function(change) {
    const input = document.getElementById('qtyInput');
    if (!input) return;
    let newVal = parseInt(input.value) + change;
    if (newVal >= PRODUCT_DATA.minOrder && newVal <= PRODUCT_DATA.maxOrder) {
        input.value = newVal;
        updateFinalPrice();
        handleQtyChange();
    }
}

const originalSetWeight = window.setWeight;
window.setWeight = function(weight, element) {
    const input = document.getElementById('weightInput');
    if (!input) return;
    input.value = weight;
    document.querySelectorAll('.weight-tag').forEach(tag => tag.classList.remove('active'));
    if (element) element.classList.add('active');
    updateFinalPrice();
    handleQtyChange();
}

window.manualWeightInput = function() {
    document.querySelectorAll('.weight-tag').forEach(tag => tag.classList.remove('active'));
    updateFinalPrice();
    // با تأخیر در initCartSystem هندل می‌شود
}

function updateFinalPrice() {
    let quantity = 0;
    const priceDisplay = document.getElementById('finalPriceDisplay');
    if (!priceDisplay) return;

    if (PRODUCT_DATA.isPackaged) {
        const qtyEl = document.getElementById('qtyInput');
        quantity = qtyEl ? parseInt(qtyEl.value) || 0 : 0;
    } else {
        const weightEl = document.getElementById('weightInput');
        quantity = weightEl ? parseFloat(weightEl.value) || 0 : 0;
    }

    const total = quantity * PRODUCT_DATA.price;
    priceDisplay.textContent = `${Math.round(total).toLocaleString('en-US')} تومان`;
}

// ============================================
// 3. Advanced Cart System
// ============================================
function initCartSystem() {
    const btn = document.querySelector('.btn-pro-cart');
    if (btn) btn.addEventListener('click', handleMainBtnClick);

    const weightInput = document.getElementById('weightInput');
    if (weightInput) {
        weightInput.addEventListener('input', () => {
            clearTimeout(typingTimer);
            typingTimer = setTimeout(handleQtyChange, 800);
        });
    }
}

function syncInputWithCart() {
    if (!PRODUCT_DATA.currentQty || PRODUCT_DATA.currentQty <= 0) return;

    if (PRODUCT_DATA.isPackaged) {
        const qtyEl = document.getElementById('qtyInput');
        if (qtyEl) {
            qtyEl.value = parseInt(PRODUCT_DATA.currentQty);
            updateFinalPrice();
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
            updateFinalPrice();
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
