export function initSafariFix() {
  const setVh = () => {
    document.documentElement.style.setProperty('--vh', `${window.innerHeight}px`);
  };
  setVh();
  window.addEventListener('resize', setVh, { passive: true });
  window.addEventListener('orientationchange', setVh, { passive: true });
}
