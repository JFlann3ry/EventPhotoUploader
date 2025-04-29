// --- Global variables for slideshow state ---
let currentSlideshowIndex = 0;
const modal = document.getElementById("modal");
const closeModal = document.getElementById("modalClose");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
// ---

// Function to clear previous modal media content
function clearModalContent() {
    const oldContent = modal.querySelector(".modal-media");
    if (oldContent) {
        modal.removeChild(oldContent);
    }
}

// --- Make openModal global ---
window.openModal = function(index) {
    // Re-query the gallery media every time the modal is opened
    const galleryMedia = Array.from(document.querySelectorAll(".gallery-item-media"));
    if (index < 0 || index >= galleryMedia.length) {
        console.error("Invalid index for openModal:", index);
        return;
    }

    currentSlideshowIndex = index; // Use the global index variable
    modal.style.display = "flex";
    clearModalContent();

    const sourceEl = galleryMedia[currentSlideshowIndex];
    let modalMedia;

    if (sourceEl.tagName.toLowerCase() === "video") {
        modalMedia = document.createElement("video");
        modalMedia.controls = true;
        modalMedia.src = sourceEl.src;
        modalMedia.autoplay = true; // Optional: start playing video on open
    } else {
        modalMedia = document.createElement("img");
        modalMedia.src = sourceEl.src;
    }
    modalMedia.classList.add("modal-media");
    // Insert the media element inside the modal before other elements (like nav buttons)
    modal.insertBefore(modalMedia, modal.firstChild);
}
// --- End global openModal ---

document.addEventListener("DOMContentLoaded", function() {
    // Note: Click listeners on individual items are now handled in gallery.js

    // Close modal when clicking on close icon
    closeModal.onclick = function() {
        modal.style.display = "none";
        const currentMedia = modal.querySelector(".modal-media");
        if (currentMedia && currentMedia.tagName.toLowerCase() === "video") {
            currentMedia.pause(); // Stop video playback on close
        }
        clearModalContent();
    };

    // Navigate to previous media
    prevBtn.onclick = function(event) {
        event.stopPropagation(); // Prevent modal click listener from firing
        const galleryMedia = Array.from(document.querySelectorAll(".gallery-item-media")); // Re-query
        let newIndex = (currentSlideshowIndex - 1 + galleryMedia.length) % galleryMedia.length;
        window.openModal(newIndex); // Use global function
    };

    // Navigate to next media
    nextBtn.onclick = function(event) {
        event.stopPropagation(); // Prevent modal click listener from firing
        const galleryMedia = Array.from(document.querySelectorAll(".gallery-item-media")); // Re-query
        let newIndex = (currentSlideshowIndex + 1) % galleryMedia.length;
        window.openModal(newIndex); // Use global function
    };

    // Close modal if clicking outside the media content (on the background)
    modal.addEventListener("click", function(e) {
        // Check if the click target is the modal background itself, not content within it
        if (e.target === modal) {
            modal.style.display = "none";
            const currentMedia = modal.querySelector(".modal-media");
             if (currentMedia && currentMedia.tagName.toLowerCase() === "video") {
                currentMedia.pause(); // Stop video playback on close
            }
            clearModalContent();
        }
    });

    // Optional: Keyboard navigation for slideshow
    document.addEventListener('keydown', function(e) {
        if (modal.style.display === 'flex') { // Only act if modal is open
            if (e.key === 'ArrowLeft') {
                prevBtn.onclick(e); // Simulate click
            } else if (e.key === 'ArrowRight') {
                nextBtn.onclick(e); // Simulate click
            } else if (e.key === 'Escape') {
                closeModal.onclick(); // Simulate click
            }
        }
    });
});