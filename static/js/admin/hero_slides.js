(function () {
  'use strict';

  function initHeroSlides(root) {
    var list = root.querySelector('[data-hero-slides-list]');
    var addBtn = root.querySelector('[data-hero-slides-add]');
    var emptyTpl = root.querySelector('[data-hero-slides-empty]');
    var totalInput = root.querySelector('input[name$="-TOTAL_FORMS"]');
    if (!list || !addBtn || !emptyTpl || !totalInput) {
      return;
    }

    var dragRow = null;

    function rows() {
      return Array.prototype.slice.call(list.querySelectorAll('[data-hero-slide-row]'));
    }

    function reindexSortOrder() {
      rows().forEach(function (row, index) {
        var orderInput = row.querySelector('input[name$="-sort_order"]');
        if (orderInput) {
          orderInput.value = String(index);
        }
      });
    }

    function bindRow(row) {
      row.addEventListener('dragstart', function (event) {
        dragRow = row;
        row.classList.add('is-dragging');
        if (event.dataTransfer) {
          event.dataTransfer.effectAllowed = 'move';
          event.dataTransfer.setData('text/plain', 'hero-slide');
        }
      });

      row.addEventListener('dragend', function () {
        row.classList.remove('is-dragging');
        rows().forEach(function (item) {
          item.classList.remove('is-drag-over');
        });
        dragRow = null;
        reindexSortOrder();
      });

      row.addEventListener('dragover', function (event) {
        event.preventDefault();
        if (!dragRow || dragRow === row) {
          return;
        }
        row.classList.add('is-drag-over');
        if (event.dataTransfer) {
          event.dataTransfer.dropEffect = 'move';
        }
      });

      row.addEventListener('dragleave', function () {
        row.classList.remove('is-drag-over');
      });

      row.addEventListener('drop', function (event) {
        event.preventDefault();
        row.classList.remove('is-drag-over');
        if (!dragRow || dragRow === row) {
          return;
        }
        var rect = row.getBoundingClientRect();
        var before = event.clientY < rect.top + rect.height / 2;
        if (before) {
          list.insertBefore(dragRow, row);
        } else {
          list.insertBefore(dragRow, row.nextSibling);
        }
        reindexSortOrder();
      });
    }

    rows().forEach(bindRow);
    reindexSortOrder();

    addBtn.addEventListener('click', function () {
      var index = parseInt(totalInput.value, 10) || 0;
      var html = emptyTpl.innerHTML.replace(/__prefix__/g, String(index));
      var wrapper = document.createElement('div');
      wrapper.innerHTML = html.trim();
      var row = wrapper.firstElementChild;
      if (!row) {
        return;
      }
      list.appendChild(row);
      totalInput.value = String(index + 1);
      bindRow(row);
      reindexSortOrder();
      var focusable = row.querySelector('input[type="file"], input[type="text"]');
      if (focusable) {
        focusable.focus();
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-hero-slides]').forEach(initHeroSlides);
  });
})();
