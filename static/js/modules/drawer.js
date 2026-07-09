export function initDrawer() {
  const drawer = document.getElementById('mobile-drawer');
  if (!drawer) return;

  const open = () => {
    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  };

  const close = () => {
    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  };

  document.querySelectorAll('[data-drawer-open]').forEach((btn) => {
    btn.addEventListener('click', open);
  });

  document.querySelectorAll('[data-drawer-close]').forEach((btn) => {
    btn.addEventListener('click', close);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
}
