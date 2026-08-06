function isTouchLike() {
  return window.matchMedia('(hover: none), (pointer: coarse)').matches;
}

export function initPhoneTooltip(root = document) {
  const btn = root.querySelector('[data-phone-tooltip]');
  if (!btn || btn.dataset.tooltipBound === '1') return;
  btn.dataset.tooltipBound = '1';

  let hideTimer = 0;

  function openTooltip() {
    btn.classList.add('is-tooltip-open');
    window.clearTimeout(hideTimer);
    hideTimer = window.setTimeout(() => {
      btn.classList.remove('is-tooltip-open');
    }, 2800);
  }

  function closeTooltip() {
    btn.classList.remove('is-tooltip-open');
    window.clearTimeout(hideTimer);
  }

  btn.addEventListener('click', (event) => {
    if (!isTouchLike()) return;
    if (btn.classList.contains('is-tooltip-open')) {
      closeTooltip();
      return;
    }
    event.preventDefault();
    openTooltip();
  });

  document.addEventListener('pointerdown', (event) => {
    if (!btn.classList.contains('is-tooltip-open')) return;
    if (btn.contains(event.target)) return;
    closeTooltip();
  });

  btn.addEventListener('blur', () => {
    if (!isTouchLike()) closeTooltip();
  });
}
