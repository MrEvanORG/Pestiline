// admin_cities.js
document.addEventListener('DOMContentLoaded', function() {
    const provinceSelect = document.querySelector('#id_province');
    const citySelect = document.querySelector('#id_city');

    if (provinceSelect && citySelect) {
        provinceSelect.addEventListener('change', function() {
            const provinceId = this.value;
            
            // پاک کردن شهرها
            citySelect.innerHTML = '<option value="">---------</option>';

            if (provinceId) {
                fetch(`/api/cities/?province_id=${provinceId}`)
                    .then(response => response.json())
                    .then(data => {
                        data.forEach(city => {
                            const option = new Option(city.name, city.id);
                            citySelect.add(option);
                        });
                    });
            }
        });
    }
});