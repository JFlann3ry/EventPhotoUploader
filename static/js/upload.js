document.getElementById('uploadForm').onsubmit = function(event) {
    event.preventDefault();

    // Retrieve event_slug and guest_id from hidden fields
    var eventSlug = document.getElementById('event_slug').value;
    var guestId = document.getElementById('guest_id').value;

    // Create FormData object
    var formData = new FormData(document.getElementById('uploadForm'));

    // Prepare the XMLHttpRequest
    var xhr = new XMLHttpRequest();
    xhr.open('POST', `/upload/${eventSlug}/${guestId}`, true);

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
