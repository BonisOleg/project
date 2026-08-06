const CLOSE_DELAY_MS = 200;

function initCatalogDropdown() {
  const root = document.querySelector('.catalog-dropdown');
  if (!root || root.dataset.bound === '1') return;
  root.dataset.bound = '1';

  const trigger = root.querySelector('.site-nav__link');
  const menu = root.querySelector('.catalog-dropdown__menu');
  if (!menu) return;

  let closeTimer = 0;

  function setOpen(open) {
    root.classList.toggle('is-open', open);
    if (trigger) trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  function openMenu() {
    window.clearTimeout(closeTimer);
    closeTimer = 0;
    setOpen(true);
  }

  function scheduleClose() {
    window.clearTimeout(closeTimer);
    closeTimer = window.setTimeout(() => {
      setOpen(false);
      closeTimer = 0;
    }, CLOSE_DELAY_MS);
  }

  if (trigger) {
    trigger.setAttribute('aria-haspopup', 'true');
    trigger.setAttribute('aria-expanded', 'false');
  }

  root.addEventListener('mouseenter', openMenu);
  root.addEventListener('mouseleave', scheduleClose);
  menu.addEventListener('mouseenter', openMenu);
  menu.addEventListener('mouseleave', scheduleClose);

  root.addEventListener('focusin', openMenu);
  root.addEventListener('focusout', (event) => {
    const next = event.relatedTarget;
    if (next instanceof Node && root.contains(next)) return;
    scheduleClose();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && root.classList.contains('is-open')) {
      setOpen(false);
      trigger?.focus();
    }
  });
}

export { initCatalogDropdown };
