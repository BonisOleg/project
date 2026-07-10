(function () {
  'use strict';

  function updateSelectedHint(input) {
    var hint = input.closest('.form-row, .flex, label, div');
    if (!hint) {
      return;
    }
    var existing = hint.querySelector('[data-bulk-images-count]');
    var count = input.files ? input.files.length : 0;
    var text = count
      ? ('Обрано файлів: ' + count)
      : '';
    if (!text) {
      if (existing) {
        existing.remove();
      }
      return;
    }
    if (!existing) {
      existing = document.createElement('span');
      existing.setAttribute('data-bulk-images-count', '1');
      existing.className = 'product-image-upload-hint';
      input.insertAdjacentElement('afterend', existing);
    }
    existing.textContent = text;
  }

  function bind(input) {
    if (input.dataset.bulkImagesBound === '1') {
      return;
    }
    input.dataset.bulkImagesBound = '1';
    input.addEventListener('change', function () {
      updateSelectedHint(input);
    });
  }

  function init(root) {
    var scope = root || document;
    scope.querySelectorAll('.product-bulk-images-input').forEach(bind);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      init(document);
    });
  } else {
    init(document);
  }

  document.addEventListener('formset:added', function (event) {
    init(event.target);
  });
})();
