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

function syncToolbarToForm(form) {
  if (!form) return;
  const sortHidden = form.querySelector('[data-filter-sort]');
  const viewHidden = form.querySelector('[data-filter-view]');
  const perPageHidden = form.querySelector('[data-filter-per-page]');
  const url = new URL(window.location.href);
  if (sortHidden) {
    sortHidden.value = url.searchParams.get('sort')
      || document.querySelector('.catalog-sort__btn.is-active')?.dataset.navValue
      || sortHidden.value
      || 'popular';
  }
  if (viewHidden) {
    viewHidden.value = url.searchParams.get('view')
      || document.querySelector('.catalog-view__btn.is-active')?.dataset.navValue
      || viewHidden.value
      || 'grid';
  }
  if (perPageHidden) {
    const grid = document.getElementById('product-grid');
    perPageHidden.value = url.searchParams.get('per_page')
      || grid?.dataset.perPage
      || perPageHidden.value
      || '12';
  }
}

export function initCatalogFilters(root = document) {
  const drawer = root.querySelector('#catalog-filter-drawer') || document.getElementById('catalog-filter-drawer');
  if (!drawer || drawer.dataset.bound === '1') {
    bindToolbarNav(root);
    bindPriceSliders(root);
    return;
  }
  drawer.dataset.bound = '1';

  const openBtns = root.querySelectorAll('[data-filter-open]');
  const closeEls = drawer.querySelectorAll('[data-filter-close]');
  const form = drawer.querySelector('[data-filter-form]');
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
      syncToolbarToForm(form);

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
      syncToolbarToForm(form);
    });
  }

  const sidebarForm = root.querySelector('[data-filter-sidebar]');
  if (sidebarForm && sidebarForm.dataset.countBound !== '1') {
    sidebarForm.dataset.countBound = '1';
    const sideSubmit = sidebarForm.querySelector('[data-filter-submit]');
    let sideAbort = null;

    async function refreshSideCount() {
      syncToolbarToForm(sidebarForm);
      const params = new URLSearchParams(new FormData(sidebarForm));
      params.delete('page');
      params.set('count_only', '1');
      const action = sidebarForm.getAttribute('action') || window.location.pathname;
      if (sideAbort) sideAbort.abort();
      sideAbort = new AbortController();
      try {
        const res = await fetch(`${action}?${params.toString()}`, {
          headers: { Accept: 'application/json' },
          signal: sideAbort.signal,
          credentials: 'same-origin',
        });
        if (!res.ok) return;
        const data = await res.json();
        if (data && typeof data.count === 'number') {
          setFilterSubmitCount(sideSubmit, data.count);
        }
      } catch (err) {
        if (err && err.name === 'AbortError') return;
      }
    }

    const scheduleSide = debounce(refreshSideCount, 250);
    sidebarForm.addEventListener('change', scheduleSide);
    sidebarForm.addEventListener('input', (event) => {
      const t = event.target;
      if (t && (t.name === 'price_min' || t.name === 'price_max')) {
        scheduleSide();
      }
    });
    sidebarForm.addEventListener('submit', () => syncToolbarToForm(sidebarForm));
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
  const controls = root.querySelectorAll('[data-catalog-nav]');
  controls.forEach((el) => {
    if (el.dataset.navBound === '1') return;
    el.dataset.navBound = '1';

    const apply = () => {
      const url = new URL(window.location.href);
      const param = el.dataset.navParam || 'sort';
      const value = el.dataset.navValue != null ? el.dataset.navValue : el.value;
      url.searchParams.set(param, value);
      url.searchParams.delete('page');
      window.location.assign(url.toString());
    };

    if (el.tagName === 'SELECT') {
      el.addEventListener('change', apply);
    } else {
      el.addEventListener('click', (event) => {
        event.preventDefault();
        if (el.classList.contains('is-active')) return;
        apply();
      });
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => initCatalogFilters(), { once: true });
} else {
  initCatalogFilters();
}
