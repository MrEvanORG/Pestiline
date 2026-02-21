// کد جاوااسکریپت شما با اصلاح نهایی
document.addEventListener("DOMContentLoaded", function () {
    // انتخاب‌گرهای جدید و دقیق
    const themeSelectors = document.querySelectorAll(".theme-selector");
    const themeStylesheet = document.getElementById("themeStylesheet");
    const footerThemeButton = document.getElementById("footerThemeButton");

    const defaultTheme = themeStylesheet.getAttribute("href");

    // تابع برای آپدیت کردن حالت فعال و متن دکمه‌ها
    function updateActiveState(selectedThemePath) {
        // ۱. ابتدا وضعیت فعال/غیرفعال را برای تمام دکمه‌ها تنظیم می‌کنیم
        themeSelectors.forEach(button => {
            if (button.getAttribute('data-theme') === selectedThemePath) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        // ۲. حالا، دکمه فعال را مشخصاً از داخل منوی فوتر پیدا می‌کنیم تا متنش را بخوانیم
        const activeFooterButton = document.querySelector('.dropdown-menu .theme-selector.active');
        
        // ۳. در نهایت، متن دکمه اصلی فوتر را فقط در صورتی که دکمه و متن آن پیدا شد، به‌روز می‌کنیم
        if (footerThemeButton && activeFooterButton) {
            const selectedThemeText = activeFooterButton.innerText;
            const iconHTML = '<i class="fa-solid fa-duotone fa-palette" aria-hidden="true"></i>';
            footerThemeButton.innerHTML = `${iconHTML} ${selectedThemeText}`;
        }
    }
    
    // تابع برای آپدیت عکس‌ها بر اساس تم
    function updateImagesBasedOnTheme(themeHref) {
        const allImages = document.querySelectorAll('.themed-image');
        let themeKey = "light"; // پیش‌فرض

        if (themeHref.includes("dark-root")) {
            themeKey = "dark";
        } else if (themeHref.includes("light-root-2")) {
            themeKey = "light2";
        }

        allImages.forEach(img => {
            const newSrc = img.getAttribute(`data-${themeKey}`);
            if (newSrc) {
                img.setAttribute("src", newSrc);
            }
        });
    }

    // تابع برای اعمال تم ذخیره‌شده در اولین بارگذاری صفحه
    function applySavedTheme() {
        const savedTheme = localStorage.getItem("selectedTheme") || defaultTheme;
        themeStylesheet.setAttribute("href", savedTheme);
        updateImagesBasedOnTheme(savedTheme);
        updateActiveState(savedTheme);
    }

    // اجرای تابع در شروع
    applySavedTheme();

    // افزودن رویداد کلیک به همه دکمه‌های انتخاب تم
    themeSelectors.forEach(button => {
        button.addEventListener("click", function () {
            const selectedTheme = this.getAttribute("data-theme");
            
            themeStylesheet.setAttribute("href", selectedTheme);
            localStorage.setItem("selectedTheme", selectedTheme);

            updateImagesBasedOnTheme(selectedTheme);
            updateActiveState(selectedTheme);
        });
    });

    // کد کنترل دکمه‌های شناور (بدون تغییر)
    const settingsMainButton = document.getElementById('settingsMainButton');
    const settingsCapsule = document.querySelector('.settings-capsule');
    const settingWrappers = document.querySelectorAll('.setting-btn-wrapper');
    const floatingSettings = document.querySelector('.floating-settings-container');
    const footer = document.querySelector('.site-footer');
    
    settingsMainButton.addEventListener('click', function(e) {
      e.stopPropagation();
      settingsCapsule.classList.toggle('expanded');
      
      if (!settingsCapsule.classList.contains('expanded')) {
        settingWrappers.forEach(wrapper => {
          wrapper.classList.remove('expanded');
        });
      }
    });
    
    settingWrappers.forEach(wrapper => {
      const settingBtn = wrapper.querySelector('.setting-btn');
      
      settingBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        wrapper.classList.toggle('expanded');
        
        settingWrappers.forEach(otherWrapper => {
          if (otherWrapper !== wrapper) {
            otherWrapper.classList.remove('expanded');
          }
        });
      });
    });
    
    document.addEventListener('click', function() {
      settingsCapsule.classList.remove('expanded');
      settingWrappers.forEach(wrapper => {
        wrapper.classList.remove('expanded');
      });
    });
    
    settingsCapsule.addEventListener('click', function(e) {
      e.stopPropagation();
    });
    
    if (footer) {
      let lastScrollPosition = 0;
      let ticking = false;
      
      const handleScroll = () => {
        const footerRect = footer.getBoundingClientRect();
        const floatingRect = floatingSettings.getBoundingClientRect();
        
        if (footerRect.top < window.innerHeight && 
            floatingRect.bottom > footerRect.top) {
          floatingSettings.classList.add('hide');
        } else {
          floatingSettings.classList.remove('hide');
        }
      };
      
      window.addEventListener('scroll', function() {
        lastScrollPosition = window.scrollY;
        
        if (!ticking) {
          window.requestAnimationFrame(function() {
            handleScroll();
            ticking = false;
          });
          
          ticking = true;
        }
      });
      
      handleScroll();
    }
});