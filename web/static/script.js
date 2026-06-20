// Auto-close flash messages
document.addEventListener('DOMContentLoaded', function() {
    const flashes = document.querySelectorAll('.flash-message');
    setTimeout(() => {
        flashes.forEach(el => el.style.display = 'none');
    }, 5000);
});

// File upload handler
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('trace-upload');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const textarea = document.getElementById('trace-input');
            if (this.files.length > 0) {
                const reader = new FileReader();
                reader.onload = function(ev) {
                    textarea.value = ev.target.result;
                };
                reader.readAsText(this.files[0]);
            }
        });
    }
});