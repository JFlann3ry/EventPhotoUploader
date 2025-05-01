document.addEventListener('DOMContentLoaded', () => {
  const gallery = document.getElementById('gallery');
  let batch = 0, totalLoaded = gallery.children.length;
  const batchSize = 20, loading = document.getElementById('loading');
  let isLoading = false, hasMoreData = true;

  const fetchImages = async () => {
    if (isLoading || !hasMoreData) return;
    isLoading = true; loading.style.display = 'block';
    try {
      const eventId = new URLSearchParams(location.search).get('event_id');
      const res = await fetch(`/api/photos/${eventId}?batch=${batch}&size=${batchSize}`);
      if (!res.ok) throw new Error();
      const images = await res.json();
      if (images.length === 0) { hasMoreData = false; return; }

      images.forEach((image, idx) => {
        const item = document.createElement('div');
        // every 3rd globally → large
        const globalIndex = totalLoaded + idx + 1;
        item.className = 'gallery-item';
        item.dataset.size = (globalIndex % 3 === 0 ? 'large' : 'small');

        const media = image.type === 'video'
          ? Object.assign(document.createElement('video'), {
              src: image.url, controls: true, className: 'gallery-item-media'
            })
          : Object.assign(document.createElement('img'), {
              src: image.url, alt: image.caption, className: 'gallery-item-media'
            });

        // only append video if can play
        if (media.tagName === 'VIDEO') {
          media.addEventListener('canplay', () => item.appendChild(media) && gallery.appendChild(item));
          media.addEventListener('error', () => {});
        } else {
          item.appendChild(media);
          gallery.appendChild(item);
        }
      });

      totalLoaded += images.length;
      batch++;
    } catch (e) {
      console.error(e);
    } finally {
      isLoading = false;
      loading.style.display = 'none';
    }
  };

  // delegate click → slideshow
  gallery.addEventListener('click', e => {
    const tgt = e.target.closest('.gallery-item-media');
    if (tgt && typeof window.openModal === 'function') {
      const items = [...document.querySelectorAll('.gallery-item-media')];
      window.openModal(items.indexOf(tgt));
    }
  });

  window.addEventListener('scroll', () => {
    if (innerHeight + scrollY >= document.body.offsetHeight - 100) fetchImages();
  });

  fetchImages();
});