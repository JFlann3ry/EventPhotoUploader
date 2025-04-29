document.addEventListener('DOMContentLoaded', () => {
    const gallery = document.getElementById('gallery');
    const loading = document.getElementById('loading');
    const eventId = new URLSearchParams(window.location.search).get('event_id');
    console.log('Event ID:', eventId);
    if (!eventId) {
        console.error('No event_id provided in the URL.');
        gallery.innerHTML = '<p>No event selected. Please select an event to view the gallery.</p>';
        return;
    }

    let currentBatch = 0;
    const batchSize = 100;
    let isLoading = false;
    let msnry; // Variable to hold the Masonry instance

    // Initialize Masonry function
    function initMasonry() {
        imagesLoaded(gallery, function() { // Wait for images before initializing
            msnry = new Masonry(gallery, {
                itemSelector: '.gallery-item',
                columnWidth: '.gallery-item', // Use item width for column calculation
                percentPosition: true, // Use percentage-based positioning (works well with % widths)
                gutter: 10 // Optional: if you want space calculated by Masonry instead of margins
            });
        });
    }

    // Fetch photos in batches
    async function fetchPhotos() {
        if (isLoading) return;
        isLoading = true;
        loading.style.display = 'block';

        try {
            const response = await fetch(`/api/photos/${eventId}?batch=${currentBatch}&size=${batchSize}`);
            if (response.ok) {
                const photos = await response.json();
                if (photos.length > 0) {
                    const fragment = document.createDocumentFragment(); // Create fragment to append efficiently
                    photos.forEach(photo => {
                        const item = createGalleryItem(photo); // Use helper function
                        fragment.appendChild(item);
                    });
                    gallery.appendChild(fragment); // Append all new items at once

                    // Tell Masonry about the new items after images are loaded
                    imagesLoaded(gallery, function() {
                        if (!msnry) { // Initialize if it's the first batch
                            initMasonry();
                        } else { // Otherwise, append and layout
                            msnry.appended(Array.from(fragment.children)); // Pass the actual elements added
                            msnry.layout(); // Recalculate layout
                        }
                    });

                    currentBatch++;
                } else {
                    loading.style.display = 'none';
                    observer.unobserve(loading);
                }
            } else {
                console.error('Failed to fetch photos');
                loading.style.display = 'none';
            }
        } catch (error) {
            console.error('Error fetching photos:', error);
            loading.style.display = 'none';
        } finally {
            isLoading = false;
        }
    }

    // Helper function to create a gallery item element
    function createGalleryItem(photo) {
        const item = document.createElement('div');
        item.classList.add('gallery-item');

        // --- REMOVE THE RANDOM LARGE ITEM LOGIC ---
        // Masonry handles layout based on natural size

        let mediaElement;
        if (photo.type === 'video') {
            mediaElement = document.createElement('video');
            mediaElement.src = photo.url;
            mediaElement.controls = true;
            mediaElement.classList.add('gallery-video', 'gallery-item-media');
        } else {
            mediaElement = document.createElement('img');
            mediaElement.src = photo.url;
            mediaElement.alt = photo.caption || 'Photo';
            mediaElement.classList.add('gallery-img', 'gallery-item-media');
            mediaElement.addEventListener('click', () => {
                const allMediaElements = Array.from(gallery.querySelectorAll('.gallery-item-media'));
                const clickedIndex = allMediaElements.indexOf(mediaElement);
                if (typeof window.openModal === 'function') {
                    window.openModal(clickedIndex);
                } else {
                    console.error("Slideshow function 'window.openModal' not found.");
                }
            });
        }
        item.appendChild(mediaElement);
        return item; // Return the created item
    }


    // Infinite scrolling
    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !isLoading) {
            fetchPhotos();
        }
    }, { threshold: 0.1 });
    observer.observe(loading);

    // Fetch the first batch of photos
    fetchPhotos();
});