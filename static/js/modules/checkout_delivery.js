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
  const upConfigured = form.dataset.upConfigured === '1';
  const npCitiesUrl = form.dataset.npCitiesUrl;
  const npWarehousesUrl = form.dataset.npWarehousesUrl;
  const upCitiesUrl = form.dataset.upCitiesUrl;
  const upPostofficesUrl = form.dataset.upPostofficesUrl;

  const cityInput = form.querySelector('[data-city-input]');
  const cityRefInput = form.querySelector('[data-city-ref]');
  const upRegionInput = form.querySelector('[data-up-region]');
  const upDistrictInput = form.querySelector('[data-up-district]');
  const cityList = form.querySelector('[data-city-list]');
  const addressInput = form.querySelector('[data-address-input]');
  const addressList = form.querySelector('[data-address-list]');
  const addressLabel = form.querySelector('[data-address-label]');
  const npBlock = form.querySelector('[data-delivery-block="np"]');
  const npNote = form.querySelector('[data-np-fallback-note]');
  const upNote = form.querySelector('[data-up-fallback-note]');

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
    if (upRegionInput) upRegionInput.value = '';
    if (upDistrictInput) upDistrictInput.value = '';
  }

  function syncServiceUi() {
    const service = selectedService();
    const isNp = service === 'nova_poshta';
    const isUp = service === 'ukrposhta';
    if (npBlock) npBlock.hidden = !isNp;
    if (npNote) npNote.hidden = !(isNp && !npConfigured);
    if (upNote) upNote.hidden = !(isUp && !upConfigured);

    if (addressLabel) {
      if (isUp) {
        addressLabel.textContent = 'Відділення Укрпошти';
        addressInput.placeholder = 'Оберіть відділення зі списку';
      } else if (selectedNpType() === 'courier') {
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
    const service = selectedService();
    if (service === 'ukrposhta') return upConfigured;
    if (service === 'nova_poshta') {
      return npConfigured && selectedNpType() !== 'courier';
    }
    return false;
  }

  const searchCities = debounce(async () => {
    const q = cityInput.value.trim();
    const service = selectedService();
    hideList(addressList);

    if (q.length < 2) {
      hideList(cityList);
      return;
    }

    if (service === 'ukrposhta') {
      if (!upConfigured) {
        hideList(cityList);
        return;
      }
      try {
        const data = await fetchJson(`${upCitiesUrl}?q=${encodeURIComponent(q)}`);
        showOptions(
          cityList,
          (data.results || []).map((row) => ({
            label: row.area ? `${row.name} (${row.area})` : row.name,
            name: row.name,
            ref: row.ref,
            regionId: row.region_id || '',
            districtId: row.district_id || '',
          })),
          (item) => {
            cityInput.value = item.name;
            if (cityRefInput) cityRefInput.value = item.ref || '';
            if (upRegionInput) upRegionInput.value = item.regionId || '';
            if (upDistrictInput) upDistrictInput.value = item.districtId || '';
            addressInput.value = '';
            searchBranches();
          },
        );
      } catch {
        hideList(cityList);
      }
      return;
    }

    if (!npConfigured) {
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
          if (upRegionInput) upRegionInput.value = '';
          if (upDistrictInput) upDistrictInput.value = '';
          addressInput.value = '';
          searchBranches();
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
    const service = selectedService();
    try {
      let url;
      if (service === 'ukrposhta') {
        const region = upRegionInput?.value || '';
        const district = upDistrictInput?.value || '';
        url = `${upPostofficesUrl}?city_ref=${encodeURIComponent(cityRef)}&q=${encodeURIComponent(q)}&region_id=${encodeURIComponent(region)}&district_id=${encodeURIComponent(district)}`;
      } else {
        const npType = selectedNpType();
        url = `${npWarehousesUrl}?city_ref=${encodeURIComponent(cityRef)}&type=${encodeURIComponent(npType)}&q=${encodeURIComponent(q)}`;
      }
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
