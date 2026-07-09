export function initHomeTabs() {
  const tabs = document.querySelector('.home-tabs');
  if (!tabs) return;

  tabs.querySelectorAll('.tabs__btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (btn.tagName === 'A') return;
      e.preventDefault();
    });
  });
}
