(function () {
  if (!localStorage.getItem('adminTheme')) {
    localStorage.setItem('adminTheme', JSON.stringify('light'));
  }
})();
