/* === Logic: Mobile Menu & Product Detail Overlay === */


// Toggle Mobile Menu
function toggleMenu() {
    document.body.classList.toggle('menu-open');
}

// Close Menu on Overlay click
document.getElementById('mobileMenuOverlay').addEventListener('click', function() {
    document.body.classList.remove('menu-open');
});

// Toggle Product Details Panel
function toggleDetails(btn) {
    const card = btn.closest('.product-card');
    
    // Close other active panels first
    if (!card.classList.contains('active')) {
        document.querySelectorAll('.product-card.active').forEach(c => {
            c.classList.remove('active');
        });
    }
    
    card.classList.toggle('active');
}

// Global listener for closing details overlay when clicking '✕'
document.querySelectorAll('.close-details').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const card = e.target.closest('.product-card');
        card.classList.remove('active');
    });
});