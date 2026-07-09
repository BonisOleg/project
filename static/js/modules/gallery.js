export function initGallery() {
  const main = document.getElementById('gallery-main');
  const thumbs = document.querySelectorAll('.product-gallery__thumb');
  if (!main || !thumbs.length) return;

  thumbs.forEach((thumb) => {
    thumb.addEventListener('click', () => {
      const src = thumb.dataset.src;
      if (!src) return;
      main.src = src;
      thumbs.forEach((t) => t.classList.toggle('is-active', t === thumb));
    });
  });
}
