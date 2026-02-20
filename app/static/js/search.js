document.querySelector('.search-input').addEventListener('keyup', function() {
    let value = this.value.toLowerCase();
    let rows = document.querySelectorAll('.user-row');

    rows.forEach(row => {
        let name = row.querySelector('.user-name').textContent.toLowerCase();
        let city = row.querySelector('.user-meta').textContent.toLowerCase();

        if (name.includes(value) || city.includes(value)) {
            row.style.display = "flex";
        } else {
            row.style.display = "none";
        }
    });
});