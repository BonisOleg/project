/**
 * Toggle видимості пароля + підказка вимог.
 */
export function initPasswordToggle() {
  document.querySelectorAll('input[data-password-toggle="1"]').forEach((input) => {
    if (input.closest('.field--password')) return;
    const field = input.closest('.field') || input.parentElement;
    if (!field) return;
    field.classList.add('field--password');

    const wrap = document.createElement('div');
    wrap.className = 'field__password-wrap';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'field__password-toggle';
    btn.setAttribute('aria-label', 'Показати пароль');
    btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
    wrap.appendChild(btn);

    btn.addEventListener('click', () => {
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-label', show ? 'Сховати пароль' : 'Показати пароль');
      btn.classList.toggle('is-open', show);
    });

    if (input.name === 'password1' || input.autocomplete === 'new-password') {
      let hint = field.querySelector('.field__hint');
      if (!hint) {
        hint = document.createElement('p');
        hint.className = 'field__hint';
        hint.textContent = 'Мінімум 8 символів, хоча б одна велика літера та одна цифра.';
        field.appendChild(hint);
      }
    }
  });
}
