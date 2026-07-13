export function initCatalogFilters(root = document) {
  const drawer = root.querySelector('#catalog-filter-drawer') || document.getElementById('catalog-filter-drawer');
  if (!drawer || drawer.dataset.bound === '1') {
    bindToolbarNav(root);
    return;
  }
  drawer.dataset.bound = '1';

  const openBtns = root.querySelectorAll('[data-filter-open]');
  const closeEls = drawer.querySelectorAll('[data-filter-close]');
  const form = drawer.querySelector('[data-filter-form]');
  const sortHidden = form?.querySelector('[data-filter-sort]');
  const perPageHidden = form?.querySelector('[data-filter-per-page]');

  function setOpen(open) {
    drawer.classList.toggle('is-open', open);
    drawer.setAttribute('aria-hidden', open ? 'false' : 'true');
    document.body.classList.toggle('catalog-filter-open', open);
    openBtns.forEach((btn) => btn.setAttribute('aria-expanded', open ? 'true' : 'false'));
  }

  openBtns.forEach((btn) => {
    btn.addEventListener('click', () => setOpen(true));
  });
  closeEls.forEach((el) => {
    el.addEventListener('click', () => setOpen(false));
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && drawer.classList.contains('is-open')) {
      setOpen(false);
    }
  });

  if (form) {
    form.addEventListener('htmx:afterRequest', () => {
      setOpen(false);
    });
    form.addEventListener('submit', () => {
      const sortSelect = document.getElementById('catalog-sort');
      const perPageSelect = document.getElementById('catalog-per-page');
      if (sortHidden && sortSelect) sortHidden.value = sortSelect.value;
      if (perPageHidden && perPageSelect) perPageHidden.value = perPageSelect.value;
    });
  }

  bindToolbarNav(root);
}

function bindToolbarNav(root = document) {
  const selects = root.querySelectorAll('[data-catalog-nav]');
  selects.forEach((select) => {
    if (select.dataset.navBound === '1') return;
    select.dataset.navBound = '1';
    select.addEventListener('change', () => {
      const url = new URL(window.location.href);
      const param = select.dataset.navParam || 'sort';
      url.searchParams.set(param, select.value);
      url.searchParams.delete('page');
      window.location.assign(url.toString());
    });
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => initCatalogFilters(), { once: true });
} else {
  initCatalogFilters();
}
