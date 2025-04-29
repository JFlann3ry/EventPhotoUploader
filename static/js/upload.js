document.getElementById('uploadForm').onsubmit = function(event) {
    event.preventDefault();

    const emailInput = document.getElementById('guest_email');
    const fileInput = document.getElementById('file_upload');
    const emailError = document.getElementById('emailError');
    const fileError = document.getElementById('fileError');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressPercentage = document.getElementById('progressPercentage');
    const uploadMessage = document.getElementById('uploadMessage');

    // Reset errors and progress
    emailError.textContent = '';
    fileError.textContent = '';
    progressContainer.style.display = 'none';
    progressBar.style.width = '0%';
    progressPercentage.textContent = '0%';
    uploadMessage.style.display = 'none';

    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(emailInput.value)) {
        emailError.textContent = 'Please enter a valid email address.';
        return;
    }

    // Validate file input
    if (fileInput.files.length === 0) {
        fileError.textContent = 'Please select at least one file to upload.';
        return;
    }

    // Create FormData object
    const formData = new FormData(document.getElementById('uploadForm'));

    // Prepare the XMLHttpRequest
    const xhr = new XMLHttpRequest();
    xhr.open('POST', window.location.pathname, true);

    // Show the progress bar container on upload start
    progressContainer.style.display = 'block';

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percent = (e.loaded / e.total) * 100;
            progressBar.style.width = percent + '%';
            progressPercentage.textContent = Math.round(percent) + '%';
        }
    });

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                // Hide progress bar and show success message
                uploadMessage.style.display = 'block';
                uploadMessage.textContent = 'Upload successful!';
                uploadMessage.style.color = 'green';
            } else {
                // Show failure message
                uploadMessage.style.display = 'block';
                uploadMessage.textContent = 'Upload failed. Please try again.';
                uploadMessage.style.color = 'red';
            }
        }
    };

    // Send the request
    xhr.send(formData);
};
