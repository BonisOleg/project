const NAME_RE = /^[A-Za-z\u0400-\u04FF]+(?:[ '\u2019-][A-Za-z\u0400-\u04FF]+)*$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PLACE_EXTRA = new Set([' ', "'", '\u2019', '.', ',', '(', ')', '-']);

function digitsOnly(value) {
  return String(value || '').replace(/\D/g, '');
}

function validPhone(value) {
  const digits = digitsOnly(value);
  if (digits.startsWith('380') && digits.length === 12) return true;
  if (digits.startsWith('0') && digits.length === 10) return true;
  return digits.length === 9;
}

function validPlace(value) {
  if (value.length < 2 || value.length > 150) return false;
  for (const ch of value) {
    if (ch >= '0' && ch <= '9') return false;
    if (PLACE_EXTRA.has(ch)) continue;
    if (!/[A-Za-z\u0400-\u04FF]/.test(ch)) return false;
  }
  return true;
}

function messageFor(input) {
  const kind = input.getAttribute('data-kind');
  const value = (input.value || '').trim();
  if (!value) {
    return input.required ? 'Заповніть поле.' : '';
  }
  if (kind === 'name' && (value.length < 2 || value.length > 100 || !NAME_RE.test(value))) {
    return 'Лише літери, пробіл, дефіс або апостроф (2–100).';
  }
  if (kind === 'phone' && !validPhone(value)) {
    return 'Вкажіть український номер, наприклад +380501112233.';
  }
  if (kind === 'email' && (value.length > 254 || !EMAIL_RE.test(value))) {
    return 'Вкажіть коректний email.';
  }
  if (kind === 'place' && !validPlace(value)) {
    return 'Вкажіть місто літерами, без цифр.';
  }
  if (kind === 'comment' && value.length > 1000) {
    return 'Коментар не довший за 1000 символів.';
  }
  if (kind === 'address' && value.length > 255) {
    return 'Адреса не довша за 255 символів.';
  }
  return '';
}

function showError(input, message) {
  const box = input.closest('.field') || input.parentElement;
  if (!box) return;
  let error = box.querySelector('.field__error');
  if (!error) {
    error = document.createElement('div');
    error.className = 'field__error';
    error.dataset.guard = '1';
    error.setAttribute('role', 'alert');
    box.appendChild(error);
  }
  error.textContent = message;
  input.setAttribute('aria-invalid', 'true');
}

function clearGuardError(input) {
  input.removeAttribute('aria-invalid');
  const box = input.closest('.field') || input.parentElement;
  const error = box && box.querySelector('.field__error[data-guard="1"]');
  if (error) error.remove();
}

function onSubmit(event) {
  const fields = event.currentTarget.querySelectorAll('[data-kind]');
  let first = null;
  fields.forEach((input) => {
    if (input.classList.contains('hp-field__input')) return;
    const message = messageFor(input);
    if (message) {
      showError(input, message);
      if (!first) first = input;
      return;
    }
    clearGuardError(input);
  });
  if (first) {
    event.preventDefault();
    first.focus();
  }
}

export function initFormGuard(root = document) {
  root.querySelectorAll('form').forEach((form) => {
    if (form.dataset.guardBound === '1') return;
    if (!form.querySelector('[data-kind]')) return;
    form.dataset.guardBound = '1';
    form.addEventListener('submit', onSubmit);
  });
}
