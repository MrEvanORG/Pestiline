document.addEventListener("DOMContentLoaded", function() {
    const timeElement = document.getElementById('jalali-time-text');
    
    function updateClock() {
        const now = new Date();
        // استفاده از fa-IR به طور خودکار اعداد را فارسی و فرمت را 24 ساعته می‌کند
        const timeString = now.toLocaleTimeString('fa-IR', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        timeElement.textContent = timeString;
    }

    // اجرای اولیه و سپس تکرار هر 1000 میلی‌ثانیه (یک ثانیه)
    if (timeElement) {
        updateClock();
        setInterval(updateClock, 1000);
    }
});