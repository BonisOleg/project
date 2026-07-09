const AUTOPLAY_MS = 5000;

export function initHeroCarousel() {
  const root = document.querySelector('[data-hero-carousel]');
  if (!root || root.dataset.heroCarouselReady === 'true') return;

  const slides = [...root.querySelectorAll('[data-hero-carousel-slide]')];
  if (slides.length < 2) return;

  root.dataset.heroCarouselReady = 'true';

  const prevBtn = root.querySelector('[data-hero-carousel-prev]');
  const nextBtn = root.querySelector('[data-hero-carousel-next]');
  const dots = [...root.querySelectorAll('[data-hero-carousel-dot]')];
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  let current = slides.findIndex((slide) => slide.classList.contains('is-active'));
  if (current < 0) current = 0;

  let timer = null;
  let isHovered = false;

  function setActive(index) {
    const nextIndex = (index + slides.length) % slides.length;
    if (nextIndex === current) return;

    slides[current].classList.remove('is-active');
    slides[nextIndex].classList.add('is-active');
    dots.forEach((dot, dotIndex) => {
      const isActive = dotIndex === nextIndex;
      dot.classList.toggle('is-active', isActive);
      dot.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
    current = nextIndex;
  }

  function next() {
    setActive(current + 1);
  }

  function prev() {
    setActive(current - 1);
  }

  function stopAutoplay() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function canAutoplay() {
    return !reducedMotion && !document.hidden && !isHovered;
  }

  function scheduleAutoplay() {
    stopAutoplay();
    if (!canAutoplay()) return;
    timer = window.setTimeout(() => {
      next();
      scheduleAutoplay();
    }, AUTOPLAY_MS);
  }

  prevBtn?.addEventListener('click', () => {
    prev();
    scheduleAutoplay();
  });

  nextBtn?.addEventListener('click', () => {
    next();
    scheduleAutoplay();
  });

  dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
      setActive(index);
      scheduleAutoplay();
    });
  });

  root.addEventListener('mouseenter', () => {
    isHovered = true;
    stopAutoplay();
  });
  root.addEventListener('mouseleave', () => {
    isHovered = false;
    scheduleAutoplay();
  });

  root.addEventListener('focusin', stopAutoplay);
  root.addEventListener('focusout', (event) => {
    if (root.contains(event.relatedTarget)) return;
    scheduleAutoplay();
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopAutoplay();
      return;
    }
    scheduleAutoplay();
  });

  window.addEventListener('pageshow', () => {
    scheduleAutoplay();
  });

  scheduleAutoplay();
}
