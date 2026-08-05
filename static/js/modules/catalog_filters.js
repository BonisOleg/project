function debounce(fn, wait) {
  let timer = 0;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), wait);
  };
}

function ukGoodsLabel(count) {
  const n = Math.abs(Number(count)) % 100;
  const n1 = n % 10;
  if (n > 10 && n < 20) return 'товарів';
  if (n1 > 1 && n1 < 5) return 'товари';
  if (n1 === 1) return 'товар';
  return 'товарів';
}

function setFilterSubmitCount(btn, count) {
  if (!btn) return;
  const n = Number(count);
  if (!Number.isFinite(n) || n < 0) return;
  btn.textContent = `Показати ${n} ${ukGoodsLabel(n)}`;
  btn.disabled = false;
  btn.dataset.resultCount = String(n);
}

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
  const submitBtn = form?.querySelector('[data-filter-submit]');

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
    let countAbort = null;

    async function refreshResultCount() {
      const sortSelect = document.getElementById('catalog-sort');
      const perPageSelect = document.getElementById('catalog-per-page');
      if (sortHidden && sortSelect) sortHidden.value = sortSelect.value;
      if (perPageHidden && perPageSelect) perPageHidden.value = perPageSelect.value;

      const params = new URLSearchParams(new FormData(form));
      params.delete('page');
      params.set('count_only', '1');

      const action = form.getAttribute('action') || window.location.pathname;
      const url = `${action}?${params.toString()}`;

      if (countAbort) countAbort.abort();
      countAbort = new AbortController();

      try {
        const res = await fetch(url, {
          headers: { Accept: 'application/json' },
          signal: countAbort.signal,
          credentials: 'same-origin',
        });
        if (!res.ok) return;
        const data = await res.json();
        if (data && typeof data.count === 'number') {
          setFilterSubmitCount(submitBtn, data.count);
        }
      } catch (err) {
        if (err && err.name === 'AbortError') return;
      }
    }

    const scheduleCount = debounce(refreshResultCount, 250);

    form.addEventListener('change', scheduleCount);
    form.addEventListener('input', (event) => {
      const t = event.target;
      if (t && (t.name === 'price_min' || t.name === 'price_max')) {
        scheduleCount();
      }
    });

    form.addEventListener('htmx:afterRequest', () => {
      setOpen(false);
      refreshResultCount();
    });

    form.addEventListener('submit', () => {
      const sortSelect = document.getElementById('catalog-sort');
      const perPageSelect = document.getElementById('catalog-per-page');
      if (sortHidden && sortSelect) sortHidden.value = sortSelect.value;
      if (perPageHidden && perPageSelect) perPageHidden.value = perPageSelect.value;
    });
  }

  bindToolbarNav(root);
  bindPriceSliders(root);
}

function bindPriceSliders(root = document) {
  root.querySelectorAll('[data-price-slider]').forEach((wrap) => {
    if (wrap.dataset.bound === '1') return;
    wrap.dataset.bound = '1';
    const form = wrap.closest('form');
    if (!form) return;
    const minRange = wrap.querySelector('[data-price-range="min"]');
    const maxRange = wrap.querySelector('[data-price-range="max"]');
    const minInput = form.querySelector('[data-price-input="min"]');
    const maxInput = form.querySelector('[data-price-input="max"]');
    if (!minRange || !maxRange || !minInput || !maxInput) return;

    function syncFromRange() {
      let minVal = Number(minRange.value);
      let maxVal = Number(maxRange.value);
      if (minVal > maxVal) {
        if (document.activeElement === minRange) maxVal = minVal;
        else minVal = maxVal;
        minRange.value = String(minVal);
        maxRange.value = String(maxVal);
      }
      minInput.value = String(minVal);
      maxInput.value = String(maxVal);
      minInput.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function syncFromInputs() {
      let minVal = Number(minInput.value || minRange.min);
      let maxVal = Number(maxInput.value || maxRange.max);
      if (minVal > maxVal) maxVal = minVal;
      minRange.value = String(minVal);
      maxRange.value = String(maxVal);
    }

    minRange.addEventListener('input', syncFromRange);
    maxRange.addEventListener('input', syncFromRange);
    minInput.addEventListener('change', syncFromInputs);
    maxInput.addEventListener('change', syncFromInputs);
  });
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
