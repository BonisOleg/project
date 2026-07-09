const COOKIE_KEY = 'oyra_cookies_accepted';
const HIDE_MS = 480;

export function initCookies() {
  const banner = document.getElementById('cookie-banner');
  if (!banner) return;

  if (localStorage.getItem(COOKIE_KEY)) {
    banner.remove();
    return;
  }

  requestAnimationFrame(() => {
    requestAnimationFrame(() => banner.classList.add('is-visible'));
  });

  const btn = banner.querySelector('[data-cookie-accept]');
  btn?.addEventListener('click', () => {
    localStorage.setItem(COOKIE_KEY, '1');
    banner.classList.remove('is-visible');
    banner.classList.add('is-hiding');
    setTimeout(() => banner.remove(), HIDE_MS);
  });
}
