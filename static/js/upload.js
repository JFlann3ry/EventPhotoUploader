document.getElementById('uploadForm').onsubmit = function(event) {
    event.preventDefault();

    // Retrieve event_slug and guest_id from hidden fields if needed (update if you use them)
    var eventSlug = document.getElementById('event_slug') ? document.getElementById('event_slug').value : '';
    var guestId = document.getElementById('guest_id') ? document.getElementById('guest_id').value : '';

    // Create FormData object
    var formData = new FormData(document.getElementById('uploadForm'));

    // Prepare the XMLHttpRequest
    var xhr = new XMLHttpRequest();
    xhr.open('POST', `/upload/${eventSlug}/${guestId}`, true);

    // Show the progress bar container on upload start
    document.getElementById('progressContainer').style.display = 'block';

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            var percent = (e.loaded / e.total) * 100;
            document.getElementById('progressBar').style.width = percent + '%';
        }
    });

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                // Hide progress bar and show success message
                document.getElementById('progressContainer').style.display = 'none';
                document.getElementById('uploadSuccess').style.display = 'block';
            } else {
                alert('Upload failed!');
            }
        }
    };

    // Send the request
    xhr.send(formData);
};
