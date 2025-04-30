document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressPercentage = document.getElementById('progressPercentage');
    const uploadMessage = document.getElementById('uploadMessage');
    const emailError = document.getElementById('emailError');
    const fileError = document.getElementById('fileError');
    const uploadBtn = form.querySelector('button[type="submit"]');

    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        // Reset messages
        emailError.textContent = '';
        fileError.textContent = '';
        uploadMessage.style.display = 'none';

        const email = form.guest_email.value.trim();
        const files = form.file_upload.files;
        if (!email) {
            emailError.textContent = 'Please enter your email.';
            return;
        }
        if (!files.length) {
            fileError.textContent = 'Please select at least one file.';
            return;
        }

        const formData = new FormData(form);

        // Show progress bar and hide upload button
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressPercentage.textContent = '0%';
        uploadBtn.style.display = 'none';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', window.location.pathname, true);

        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percent + '%';
                progressPercentage.textContent = percent + '%';
            }
        };

        xhr.onload = function() {
            uploadBtn.style.display = 'block';
            if (xhr.status === 200) {
                progressBar.style.width = '100%';
                progressPercentage.textContent = '100%';
                uploadMessage.style.display = 'block';
                uploadMessage.textContent = 'Upload successful!';
                uploadMessage.className = 'upload-message success-message';
                form.reset();
            } else {
                uploadMessage.style.display = 'block';
                uploadMessage.textContent = 'Upload failed. Please try again.';
                uploadMessage.className = 'upload-message error-message';
            }
        };

        xhr.onerror = function() {
            uploadBtn.style.display = 'block';
            uploadMessage.style.display = 'block';
            uploadMessage.textContent = 'Upload failed. Please try again.';
            uploadMessage.className = 'upload-message error-message';
        };

        xhr.send(formData);
    });
});
