document.getElementById('uploadForm').onsubmit = function(event) {
    event.preventDefault();
    
    // Retrieve event_slug and guest_id from hidden fields
    var eventSlug = document.getElementById('event_slug').value;
    var guestId = document.getElementById('guest_id').value;

    // Debugging logs
    console.log('Event Slug:', eventSlug);
    console.log('Guest ID:', guestId);

    // Create FormData object
    var formData = new FormData(document.getElementById('uploadForm'));
    
    // Log formData to ensure file upload is included
    console.log('Form data:', formData);

    // Prepare the XMLHttpRequest
    var xhr = new XMLHttpRequest();
    xhr.open('POST', `/upload/${eventSlug}/${guestId}`, true);

    // Log the full URL for debugging
    console.log('Sending request to:', `/upload/${eventSlug}/${guestId}`);

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            var percent = (e.loaded / e.total) * 100;
            document.getElementById('progressBar').style.width = percent + '%';
        }
    });

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                alert('Upload complete!');
            } else {
                alert('Upload failed!');
            }
        }
    };

    // Send the request
    xhr.send(formData);
    document.querySelector('.progress').style.display = 'block';
};
