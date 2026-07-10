(function () {
  function submitFilterForm(form) {
    if (!form) return;
    form.submit();
  }

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('filter-form');
    if (!form) return;

    form.addEventListener('change', function (event) {
      if (event.target && event.target.matches('select, input')) {
        submitFilterForm(form);
      }
    });

    if (window.django && django.jQuery) {
      django.jQuery(form).on('select2:select select2:clear', 'select', function () {
        submitFilterForm(form);
      });
    }
  });
})();
