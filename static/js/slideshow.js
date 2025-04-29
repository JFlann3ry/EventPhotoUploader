document.addEventListener("DOMContentLoaded", function() {
    // Gather all gallery media (images and videos) into an array
    const galleryMedia = Array.from(document.querySelectorAll(".gallery-item-media"));
    const modal = document.getElementById("modal");
    const closeModal = document.getElementById("modalClose");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
  
    let currentIndex = 0;

    // Function to clear previous modal media content
    function clearModalContent() {
        const oldContent = modal.querySelector(".modal-media");
        if (oldContent) {
            modal.removeChild(oldContent);
        }
    }

    // Function to open modal with a given index; clones the element based on its type
    function openModal(index) {
        currentIndex = index;
        modal.style.display = "flex";
        clearModalContent();
        const sourceEl = galleryMedia[currentIndex];
        let modalMedia;
        if (sourceEl.tagName.toLowerCase() === "video") {
            modalMedia = document.createElement("video");
            modalMedia.controls = true;
            modalMedia.src = sourceEl.src;
        } else {
            modalMedia = document.createElement("img");
            modalMedia.src = sourceEl.src;
        }
        modalMedia.classList.add("modal-media");
        // Insert the media element inside the modal before other elements (if any)
        modal.insertBefore(modalMedia, modal.firstChild);
    }

    // Event listener for clicking on gallery media
    galleryMedia.forEach((media, index) => {
        media.addEventListener("click", () => openModal(index));
    });

    // Close modal when clicking on close icon
    closeModal.onclick = function() {
        modal.style.display = "none";
        clearModalContent();
    };

    // Navigate to previous media
    prevBtn.onclick = function(event) {
        event.stopPropagation();
        currentIndex = (currentIndex - 1 + galleryMedia.length) % galleryMedia.length;
        openModal(currentIndex);
    };

    // Navigate to next media
    nextBtn.onclick = function(event) {
        event.stopPropagation();
        currentIndex = (currentIndex + 1) % galleryMedia.length;
        openModal(currentIndex);
    };

    // Close modal if clicking outside the media
    modal.addEventListener("click", function(e) {
        if (e.target === modal) {
            modal.style.display = "none";
            clearModalContent();
        }
    });
});