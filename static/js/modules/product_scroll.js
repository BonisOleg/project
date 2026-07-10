function getScrollStep(viewport) {
  const item = viewport.querySelector('.product-grid__item');
  if (!item) return viewport.clientWidth * 0.7;

  const grid = item.parentElement;
  const styles = grid ? getComputedStyle(grid) : null;
  const gapRaw = styles ? styles.columnGap || styles.gap : '0';
  const gap = Number.parseFloat(gapRaw) || 0;
  return item.getBoundingClientRect().width + gap;
}

function updateButtons(viewport, prevBtn, nextBtn) {
  const maxScroll = viewport.scrollWidth - viewport.clientWidth;
  const left = viewport.scrollLeft;
  const epsilon = 4;

  prevBtn.disabled = left <= epsilon;
  nextBtn.disabled = left >= maxScroll - epsilon;
}

function remeasureScrollable(root, viewport, prevBtn, nextBtn) {
  // Міряємо в peek-режимі, інакше flex-grow ховає реальний overflow
  root.dataset.scrollable = '1';
  void viewport.offsetWidth;

  const maxScroll = viewport.scrollWidth - viewport.clientWidth;
  const scrollable = maxScroll > 4;
  root.dataset.scrollable = scrollable ? '1' : '0';

  if (!scrollable) {
    prevBtn.disabled = true;
    nextBtn.disabled = true;
    if (viewport.scrollLeft !== 0) {
      viewport.scrollLeft = 0;
    }
    return;
  }

  updateButtons(viewport, prevBtn, nextBtn);
}

function scrollByCard(viewport, direction) {
  viewport.scrollBy({ left: direction * getScrollStep(viewport), behavior: 'smooth' });
}

function bindScroll(root) {
  if (root.dataset.scrollBound === '1') return;
  root.dataset.scrollBound = '1';

  const viewport = root.querySelector('.product-scroll__viewport');
  const prevBtn = root.querySelector('.product-scroll__btn--prev');
  const nextBtn = root.querySelector('.product-scroll__btn--next');
  if (!viewport || !prevBtn || !nextBtn) return;

  const syncButtons = () => updateButtons(viewport, prevBtn, nextBtn);
  const syncOverflow = () => remeasureScrollable(root, viewport, prevBtn, nextBtn);

  prevBtn.addEventListener('click', () => scrollByCard(viewport, -1));
  nextBtn.addEventListener('click', () => scrollByCard(viewport, 1));
  viewport.addEventListener('scroll', syncButtons, { passive: true });
  window.addEventListener('resize', syncOverflow, { passive: true });

  if (typeof ResizeObserver !== 'undefined') {
    const ro = new ResizeObserver(syncOverflow);
    ro.observe(viewport);
  }

  // Після layout / шрифтів — повторна перевірка (iOS Safari)
  requestAnimationFrame(() => {
    syncOverflow();
    requestAnimationFrame(syncOverflow);
  });
  syncOverflow();
}

export function initProductScroll(scope = document) {
  scope.querySelectorAll('[data-product-scroll]').forEach(bindScroll);
}
