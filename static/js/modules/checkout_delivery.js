function debounce(fn, wait = 280) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

function initCheckoutDelivery() {
  const form = document.querySelector('[data-delivery-form]');
  if (!form || form.dataset.bound === '1') return;
  form.dataset.bound = '1';

  const npConfigured = form.dataset.npConfigured === '1';
  const npCitiesUrl = form.dataset.npCitiesUrl;
  const npWarehousesUrl = form.dataset.npWarehousesUrl;

  const cityInput = form.querySelector('[data-city-input]');
  const cityRefInput = form.querySelector('[data-city-ref]');
  const cityList = form.querySelector('[data-city-list]');
  const addressInput = form.querySelector('[data-address-input]');
  const addressList = form.querySelector('[data-address-list]');
  const addressLabel = form.querySelector('[data-address-label]');
  const npBlock = form.querySelector('[data-delivery-block="np"]');
  const npNote = form.querySelector('[data-np-fallback-note]');

  function selectedService() {
    const checked = form.querySelector('input[name="delivery_service"]:checked');
    return checked ? checked.value : 'nova_poshta';
  }

  function selectedNpType() {
    const checked = form.querySelector('input[name="delivery_type"]:checked');
    return checked ? checked.value : 'warehouse';
  }

  function clearCityMeta() {
    if (cityRefInput) cityRefInput.value = '';
  }

  function syncServiceUi() {
    const service = selectedService();
    const isNp = service === 'nova_poshta';
    const isCourier = service === 'courier_delivery';

    if (npBlock) npBlock.hidden = !isNp;
    if (npNote) npNote.hidden = !(isNp && !npConfigured);

    if (!addressLabel || !addressInput) return;

    if (isCourier) {
      addressLabel.textContent = 'Адреса доставки';
      addressInput.placeholder = 'Вулиця, будинок, квартира';
      return;
    }

    if (selectedNpType() === 'courier') {
      addressLabel.textContent = 'Адреса доставки';
      addressInput.placeholder = 'Вулиця, будинок, квартира';
    } else if (selectedNpType() === 'postomat') {
      addressLabel.textContent = 'Поштомат';
      addressInput.placeholder = 'Оберіть поштомат зі списку';
    } else {
      addressLabel.textContent = 'Відділення Нової Пошти';
      addressInput.placeholder = 'Оберіть відділення зі списку';
    }
  }

  function hideList(list) {
    if (!list) return;
    list.hidden = true;
    list.innerHTML = '';
  }

  function showOptions(list, items, onPick) {
    if (!list) return;
    list.innerHTML = '';
    if (!items.length) {
      hideList(list);
      return;
    }
    items.forEach((item) => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'searchable-select__option';
      btn.textContent = item.label;
      btn.addEventListener('mousedown', (event) => {
        event.preventDefault();
        onPick(item);
        hideList(list);
      });
      li.appendChild(btn);
      list.appendChild(li);
    });
    list.hidden = false;
  }

  async function fetchJson(url) {
    const response = await fetch(url, {
      headers: { Accept: 'application/json' },
      credentials: 'same-origin',
    });
    if (!response.ok) throw new Error('request_failed');
    return response.json();
  }

  function canSearchBranches() {
    return (
      selectedService() === 'nova_poshta'
      && npConfigured
      && selectedNpType() !== 'courier'
    );
  }

  const searchCities = debounce(async () => {
    const q = cityInput.value.trim();
    hideList(addressList);

    if (q.length < 2) {
      hideList(cityList);
      return;
    }

    if (selectedService() !== 'nova_poshta' || !npConfigured) {
      hideList(cityList);
      return;
    }

    try {
      const data = await fetchJson(`${npCitiesUrl}?q=${encodeURIComponent(q)}`);
      showOptions(
        cityList,
        (data.results || []).map((row) => ({
          label: row.area ? `${row.name} (${row.area})` : row.name,
          name: row.name,
          ref: row.ref,
        })),
        (item) => {
          cityInput.value = item.name;
          if (cityRefInput) cityRefInput.value = item.ref || '';
          hideList(cityList);
          if (canSearchBranches()) searchBranches();
        },
      );
    } catch {
      hideList(cityList);
    }
  });

  const searchBranches = debounce(async () => {
    if (!canSearchBranches()) {
      hideList(addressList);
      return;
    }
    const cityRef = cityRefInput?.value || '';
    if (!cityRef) {
      hideList(addressList);
      return;
    }
    const q = addressInput.value.trim();
    try {
      const npType = selectedNpType();
      const url = `${npWarehousesUrl}?city_ref=${encodeURIComponent(cityRef)}&type=${encodeURIComponent(npType)}&q=${encodeURIComponent(q)}`;
      const data = await fetchJson(url);
      showOptions(
        addressList,
        (data.results || []).map((row) => ({
          label: row.name,
          name: row.name,
        })),
        (item) => {
          addressInput.value = item.name;
        },
      );
    } catch {
      hideList(addressList);
    }
  });

  form.querySelectorAll('input[name="delivery_service"]').forEach((input) => {
    input.addEventListener('change', () => {
      hideList(cityList);
      hideList(addressList);
      clearCityMeta();
      cityInput.value = '';
      addressInput.value = '';
      syncServiceUi();
    });
  });

  form.querySelectorAll('input[name="delivery_type"]').forEach((input) => {
    input.addEventListener('change', () => {
      hideList(addressList);
      addressInput.value = '';
      syncServiceUi();
      if (canSearchBranches()) searchBranches();
    });
  });

  cityInput.addEventListener('input', () => {
    clearCityMeta();
    searchCities();
  });
  cityInput.addEventListener('focus', () => {
    if (cityInput.value.trim()) searchCities();
  });
  cityInput.addEventListener('blur', () => {
    setTimeout(() => hideList(cityList), 150);
  });

  addressInput.addEventListener('input', () => {
    if (canSearchBranches()) searchBranches();
    else hideList(addressList);
  });
  addressInput.addEventListener('focus', () => {
    if (canSearchBranches()) searchBranches();
  });
  addressInput.addEventListener('blur', () => {
    setTimeout(() => hideList(addressList), 150);
  });

  syncServiceUi();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initCheckoutDelivery, { once: true });
} else {
  initCheckoutDelivery();
}
