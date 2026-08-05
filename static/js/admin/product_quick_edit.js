(function () {
  'use strict';

  function csrfToken() {
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function statusEl(control) {
    var cell = control.closest('td') || control.parentElement;
    return cell ? cell.querySelector('.oyra-quick-status') : null;
  }

  function setStatus(control, text, ok) {
    var el = statusEl(control);
    if (!el) return;
    el.textContent = text;
    el.classList.toggle('is-ok', !!ok);
    el.classList.toggle('is-err', !ok);
  }

  function save(control, payload) {
    var id = control.getAttribute('data-product-id');
    if (!id) return;
    setStatus(control, '…', true);
    fetch('/catalog/admin/product-quick-update/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
      },
      body: JSON.stringify(Object.assign({ id: Number(id) }, payload)),
    })
      .then(function (res) { return res.json().then(function (data) { return { res: res, data: data }; }); })
      .then(function (result) {
        if (!result.res.ok || !result.data.ok) {
          setStatus(control, (result.data && result.data.error) || 'Помилка', false);
          return;
        }
        setStatus(control, '✓', true);
        window.setTimeout(function () { setStatus(control, '', true); }, 1500);
      })
      .catch(function () {
        setStatus(control, 'Помилка мережі', false);
      });
  }

  document.addEventListener('change', function (e) {
    var select = e.target.closest('.oyra-quick-availability');
    if (!select) return;
    save(select, { availability: select.value });
  });

  document.addEventListener('keydown', function (e) {
    var input = e.target.closest('.oyra-quick-price');
    if (!input || e.key !== 'Enter') return;
    e.preventDefault();
    input.blur();
  });

  document.addEventListener('focusout', function (e) {
    var input = e.target.closest('.oyra-quick-price');
    if (!input) return;
    if (input.dataset.lastSaved === input.value) return;
    input.dataset.lastSaved = input.value;
    save(input, { price: input.value });
  });

  document.querySelectorAll('.oyra-quick-price').forEach(function (input) {
    input.dataset.lastSaved = input.value;
  });
})();
