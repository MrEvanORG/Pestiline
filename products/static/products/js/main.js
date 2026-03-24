/* === Logic: Mobile Menu & Product Detail Overlay === */

// Toggle Mobile Menu
function toggleMenu() {
    document.body.classList.toggle('menu-open');
}

// Close Menu on Overlay click (ایمن شده)
const mobileOverlay = document.getElementById('mobileMenuOverlay');
if (mobileOverlay) {
    mobileOverlay.addEventListener('click', function() {
        document.body.classList.remove('menu-open');
    });
}

// Toggle Product Details Panel
function toggleDetails(btn) {
    const card = btn.closest('.product-card');
    if (!card) return; // ایمن شده
    
    // Close other active panels first
    if (!card.classList.contains('active')) {
        document.querySelectorAll('.product-card.active').forEach(c => {
            c.classList.remove('active');
        });
    }
    
    card.classList.toggle('active');
}

// Global listener for closing details overlay when clicking '✕'
const closeBtns = document.querySelectorAll('.close-details');
if (closeBtns.length > 0) {
    closeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const card = e.target.closest('.product-card');
            if (card) card.classList.remove('active');
        });
    });
}

// اسکرول نرم به بالا برای لینک‌های با href="#"
document.querySelectorAll('a[href="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault(); // جلوگیری از پرش ناگهانی مرورگر
        
        window.scrollTo({
            top: 0,
            behavior: 'smooth' // اسکرول نرم
        });
    });
});
