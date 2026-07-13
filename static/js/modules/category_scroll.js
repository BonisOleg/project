function getScrollStep(viewport) {
  const item = viewport.querySelector('.category-scroll__item');
  if (!item) return Math.max(viewport.clientWidth * 0.55, 120);

  const track = item.parentElement;
  const styles = track ? getComputedStyle(track) : null;
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

function remeasure(root, viewport, prevBtn, nextBtn) {
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

function scrollByItem(viewport, direction) {
  viewport.scrollBy({ left: direction * getScrollStep(viewport), behavior: 'smooth' });
}

function bindScroll(root) {
  if (root.dataset.scrollBound === '1') return;
  root.dataset.scrollBound = '1';

  const viewport = root.querySelector('.category-scroll__viewport');
  const prevBtn = root.querySelector('.category-scroll__btn--prev');
  const nextBtn = root.querySelector('.category-scroll__btn--next');
  if (!viewport || !prevBtn || !nextBtn) return;

  const syncButtons = () => updateButtons(viewport, prevBtn, nextBtn);
  const syncOverflow = () => remeasure(root, viewport, prevBtn, nextBtn);

  prevBtn.addEventListener('click', () => scrollByItem(viewport, -1));
  nextBtn.addEventListener('click', () => scrollByItem(viewport, 1));
  viewport.addEventListener('scroll', syncButtons, { passive: true });
  window.addEventListener('resize', syncOverflow, { passive: true });

  if (typeof ResizeObserver !== 'undefined') {
    const ro = new ResizeObserver(syncOverflow);
    ro.observe(viewport);
  }

  requestAnimationFrame(() => {
    syncOverflow();
    requestAnimationFrame(syncOverflow);
  });
  syncOverflow();
}

export function initCategoryScroll(scope = document) {
  scope.querySelectorAll('[data-category-scroll]').forEach(bindScroll);
}
