document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('togglePassword');
    if (toggleBtn) {
        toggleBtn.onclick = function() {
            const pw = document.getElementById('password');
            if (pw.type === "password") {
                pw.type = "text";
                this.textContent = "Hide";
            } else {
                pw.type = "password";
                this.textContent = "Show";
            }
        };
    }
});