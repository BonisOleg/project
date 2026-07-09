export function initProductTabs() {
  const nav = document.querySelector('.product-tabs__nav');
  if (!nav) return;

  const buttons = nav.querySelectorAll('[data-tab]');
  const panels = document.querySelectorAll('[data-panel]');

  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.tab;
      buttons.forEach((b) => b.classList.toggle('is-active', b === btn));
      panels.forEach((p) => {
        p.hidden = p.dataset.panel !== id;
      });
    });
  });
}
