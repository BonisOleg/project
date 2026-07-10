import { initDrawer } from './modules/drawer.js';
import { initReveal } from './modules/reveal.js';
import { initSafariFix } from './modules/safari_fix.js?v=20260701';
import { initCookies } from './modules/cookies.js';
import { initProductTabs } from './modules/product_tabs.js';
import { initGallery } from './modules/gallery.js';
import { initHeroCarousel } from './modules/hero_carousel.js?v=20260703f';
import { initHomeTabs } from './modules/home_tabs.js';
import { initProductScroll } from './modules/product_scroll.js';
import { initToasts } from './modules/toast.js';

function onReady(callback) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', callback, { once: true });
    return;
  }
  callback();
}

onReady(() => {
  initSafariFix();
  initDrawer();
  initReveal();
  initCookies();
  initProductTabs();
  initGallery();
  initHeroCarousel();
  initHomeTabs();
  initProductScroll();
  initToasts();
});

document.body.addEventListener('htmx:configRequest', (event) => {
  const source = event.detail.elt;
  const token = source?.closest('form')?.querySelector('[name=csrfmiddlewaretoken]')
    || document.querySelector('[name=csrfmiddlewaretoken]');
  if (token) {
    event.detail.headers['X-CSRFToken'] = token.value;
  }
});

document.body.addEventListener('htmx:afterSwap', (event) => {
  const target = event.detail?.target;
  if (target?.id === 'home-products-panel') {
    initProductScroll(target);
  }
  initToasts(document.getElementById('toast-root') || document);
});

document.body.addEventListener('htmx:oobAfterSwap', (event) => {
  initToasts(event.detail?.target || document);
});
