const TOAST_TTL_MS = 3200;
const TOAST_OUT_MS = 200;

function dismissToast(el) {
  if (!el || el.dataset.toastLeaving === '1') return;
  el.dataset.toastLeaving = '1';
  el.classList.add('message--out');
  window.setTimeout(() => {
    el.remove();
  }, TOAST_OUT_MS);
}

function bindToast(el) {
  if (!(el instanceof HTMLElement) || el.dataset.toastBound === '1') return;
  el.dataset.toastBound = '1';
  window.setTimeout(() => dismissToast(el), TOAST_TTL_MS);
}

export function initToasts(scope = document) {
  const root = scope instanceof Element ? scope : document;
  if (root.matches?.('[data-toast]')) {
    bindToast(root);
  }
  root.querySelectorAll?.('[data-toast]').forEach(bindToast);
}
