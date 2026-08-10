/**
 * Індикатор прогресу імпорту постачальника (синхронний POST).
 * Показує бар і таймер, поки сторінка не перезавантажиться з результатом.
 */
(function () {
  'use strict';

  function init() {
    var form = document.querySelector('.supplier-import__form');
    if (!form || form.dataset.progressBound === '1') {
      return;
    }
    form.dataset.progressBound = '1';

    var overlay = document.getElementById('supplier-import-progress');
    var elapsedEl = document.getElementById('supplier-import-elapsed');
    var submitBtn = form.querySelector('.supplier-import__submit');
    var fileInput = form.querySelector('input[type="file"]');
    var clientError = document.getElementById('supplier-import-client-error');
    var timerId = null;

    function showClientError(text) {
      if (!clientError) {
        return;
      }
      clientError.textContent = text;
      clientError.hidden = false;
    }

    function hideClientError() {
      if (!clientError) {
        return;
      }
      clientError.hidden = true;
      clientError.textContent = '';
    }

    form.addEventListener('submit', function (event) {
      hideClientError();

      if (fileInput && (!fileInput.files || !fileInput.files.length)) {
        event.preventDefault();
        showClientError(
          'Спочатку оберіть файл вигрузки (.xlsx, .csv або .json), потім натисніть «Завантажити та імпортувати».',
        );
        return;
      }

      if (!overlay) {
        return;
      }

      overlay.hidden = false;
      overlay.setAttribute('aria-busy', 'true');
      document.body.classList.add('supplier-import-busy');

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.setAttribute('aria-disabled', 'true');
        submitBtn.textContent = 'Імпорт триває…';
      }

      var started = Date.now();
      if (elapsedEl) {
        elapsedEl.textContent = '0';
      }
      if (timerId) {
        window.clearInterval(timerId);
      }
      timerId = window.setInterval(function () {
        if (!elapsedEl) {
          return;
        }
        var sec = Math.floor((Date.now() - started) / 1000);
        elapsedEl.textContent = String(sec);
      }, 250);
    });

    var report = document.getElementById('supplier-import-report');
    if (report) {
      report.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
