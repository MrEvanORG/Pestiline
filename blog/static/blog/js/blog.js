document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // --- 1. Smart Image Gallery (گالری هوشمند) ---
    // ============================================================
    // این بخش باید قبل از TOC اجرا شود تا اگر گالری‌ها ساختار صفحه را تغییر دادند، 
    // محاسبات اسکرول TOC دچار خطا نشود.
    const postContent = document.getElementById('postContent');
    
    if (postContent) {
        // تبدیل فرزندان به یک آرایه ثابت تا تغییرات DOM در حین حلقه مشکلی ایجاد نکند
        const children = Array.from(postContent.children);
        let galleryGroup = [];

        // تابع پردازش و گروه‌بندی عکس‌های متوالی
        const processGalleryGroup = () => {
            if (galleryGroup.length === 0) return;

            const count = galleryGroup.length;
            const firstItem = galleryGroup[0];

            if (count === 1) {
                // اگر فقط یک عکس بود، به عنوان تصویر عادی نمایش داده شود
                firstItem.className = 'post-block post-block--image';
            } else {
                // اگر ۲ عکس یا بیشتر بود، ساختار گرید (گالری) ساخته شود
                const wrapper = document.createElement('div');
                wrapper.className = 'post-gallery-wrapper';
                
                const grid = document.createElement('div');
                grid.className = 'post-gallery-grid';
                // تنظیم ویژگی data-count برای CSS (محدود به نهایتاً 6 استایل در CSS شما)
                grid.setAttribute('data-count', count > 6 ? 6 : count); 

                // قرار دادن کانتینر گالری درست قبل از اولین عکس در DOM
                postContent.insertBefore(wrapper, firstItem);

                // انتقال عکس‌ها به داخل گرید
                galleryGroup.forEach(item => {
                    item.className = ''; // حذف کلاس raw-gallery-item
                    grid.appendChild(item);
                });

                wrapper.appendChild(grid);
            }
            
            // ریست کردن گروه برای گالری‌های بعدی در صفحه
            galleryGroup = []; 
        };

        children.forEach(child => {
            // اگر المان دارای کلاس raw-gallery-item بود، به گروه اضافه می‌شود
            if (child.classList.contains('raw-gallery-item')) {
                galleryGroup.push(child);
            } else {
                // با رسیدن به یک المان دیگر (مثل پاراگراف یا تیتر)، گروه قبلی بسته و پردازش می‌شود
                processGalleryGroup();
            }
        });

        // پردازش گروه آخر در صورتی که مقاله با عکس‌های گالری تمام شده باشد
        processGalleryGroup();
    }
    // ============================================================
    // --- 5. Convert Raw Text to Elegant List (تبدیل متن به لیست) ---
    // ============================================================
    const rawLists = document.querySelectorAll('.raw-text-list');
    
    rawLists.forEach(listDiv => {
        // گرفتن متن خام از داخل div
        const textContent = listDiv.textContent || listDiv.innerText;
        
        // تکه کردن متن بر اساس ENTER (\n) و حذف خطوط خالی
        const items = textContent.split(/\r?\n/)
            .map(item => item.trim())
            .filter(item => item.length > 0);
            
        if (items.length > 0) {
            // ساخت عنصر <ul>
            const ul = document.createElement('ul');
            ul.className = 'post-list-elegant';
            
            // ساخت <li> برای هر خط
            items.forEach(itemText => {
                const li = document.createElement('li');
                li.textContent = itemText;
                ul.appendChild(li);
            });
            
            // پاک کردن متن خام اولیه و جایگذاری لیست زیبای ساخته شده
            listDiv.innerHTML = '';
            listDiv.appendChild(ul);
        }
    });

    // ============================================================
    // --- 2. Table of Contents (TOC) ---
    // ============================================================
    const tocListContainer = document.getElementById('tocList');
    const tocWidget = document.getElementById('tocWidget');

    // بررسی وجود داده و المان‌های مورد نیاز
    if (
        typeof djangoTOCData !== 'undefined' &&
        djangoTOCData.length > 0 &&
        tocListContainer
    ) {
        tocListContainer.innerHTML = '';

        // ساخت لینک‌های TOC
        djangoTOCData.forEach(function (heading) {
            const a = document.createElement('a');
            a.href = '#' + heading.id;
            a.textContent = heading.text;
            a.className = 'toc-item';

            if (heading.level === 3) {
                a.classList.add('toc-item--h3');
            }

            // کلیک روی آیتم TOC → اسکرول نرم به heading
            a.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation(); // جلوگیری از تداخل با اسکریپت اصلی

                const targetElement = document.getElementById(heading.id);
                if (targetElement) {
                    // 100px فاصله از بالا برای نوار ناوبری
                    const offsetPosition =
                        targetElement.getBoundingClientRect().top +
                        window.pageYOffset -
                        100;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth',
                    });
                }
            });

            tocListContainer.appendChild(a);
        });

        // نمایش ویجت TOC
        if (tocWidget) {
            tocWidget.style.display = 'block';
        }

        // --- Scroll Spy: هایلایت آیتم فعال TOC ---
        const tocLinks = tocListContainer.querySelectorAll('a.toc-item');

        window.addEventListener('scroll', function () {
            let currentId = '';

            djangoTOCData.forEach(function (heading) {
                const el = document.getElementById(heading.id);
                if (el) {
                    const rect = el.getBoundingClientRect();
                    // هدینگی که از بالای صفحه گذشته (با کمی حاشیه)
                    if (rect.top < 150) {
                        currentId = heading.id;
                    }
                }
            });

            tocLinks.forEach(function (link) {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + currentId) {
                    link.classList.add('active');
                }
            });
        });

    } else {
        // اگر TOC داده‌ای نداشت، ویجت رو مخفی کن
        if (tocWidget) {
            tocWidget.style.display = 'none';
        }
    }


    // ============================================================
    // --- 3. Reading Progress Bar ---
    // ============================================================
    const progressBar = document.getElementById('readingProgressBar');

    if (progressBar) {
        window.addEventListener('scroll', function () {
            const scrollTop =
                window.scrollY || document.documentElement.scrollTop;

            const scrollHeight =
                document.documentElement.scrollHeight -
                document.documentElement.clientHeight;

            if (scrollHeight > 0) {
                const scrollPercentage = (scrollTop / scrollHeight) * 100;
                progressBar.style.width = scrollPercentage + '%';
            }
        });
    }


    // ============================================================
    // --- 4. Copy Link Button ---
    // ============================================================
    const copyLinkBtn = document.getElementById('copy-link-btn');
    const copyToast = document.getElementById('copyToast');

    if (copyLinkBtn && copyToast) {
        copyLinkBtn.addEventListener('click', function () {
            const url = this.dataset.url || window.location.href;

            // استفاده از Clipboard API مدرن
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(function () {
                    showCopyToast();
                }).catch(function () {
                    // fallback در صورت خطا
                    fallbackCopyText(url);
                });
            } else {
                // fallback برای مرورگرهای قدیمی‌تر
                fallbackCopyText(url);
            }
        });
    }

    function showCopyToast() {
        if (!copyToast) return;
        copyToast.classList.add('show');
        setTimeout(function () {
            copyToast.classList.remove('show');
        }, 3000);
    }

    // روش قدیمی کپی برای مرورگرهای قدیمی
    function fallbackCopyText(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            showCopyToast();
        } catch (err) {
            console.warn('کپی لینک ناموفق بود:', err);
        }

        document.body.removeChild(textArea);
    }

});
