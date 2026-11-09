/**
 * Push GA4 purchase + Enhanced Conversions user_data once per transaction_id.
 * Anti-dupe: sessionStorage + cookie (Safari / private mode fallback).
 */

const STORAGE_PREFIX = 'oyra_ps_';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

function storageKey(transactionId) {
  const safe = String(transactionId).replace(/[^A-Za-z0-9_-]/g, '');
  return `${STORAGE_PREFIX}${safe}`;
}

function alreadySent(transactionId) {
  const key = storageKey(transactionId);
  try {
    if (window.sessionStorage && sessionStorage.getItem(key) === '1') {
      return true;
    }
  } catch (_) {
    /* private mode / blocked */
  }
  const needle = `${key}=1`;
  return document.cookie.split(';').some((part) => part.trim().startsWith(needle));
}

function markSent(transactionId) {
  const key = storageKey(transactionId);
  try {
    if (window.sessionStorage) {
      sessionStorage.setItem(key, '1');
    }
  } catch (_) {
    /* ignore */
  }
  document.cookie = `${key}=1; path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`;
}

export function initPurchaseDataLayer() {
  const node = document.getElementById('oyra-purchase-datalayer');
  if (!node) return;

  let payload;
  try {
    payload = JSON.parse(node.textContent);
  } catch (_) {
    return;
  }

  const transactionId = payload?.ecommerce?.transaction_id;
  if (!transactionId || alreadySent(String(transactionId))) {
    return;
  }

  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ ecommerce: null });
  window.dataLayer.push(payload);
  markSent(String(transactionId));
}

initPurchaseDataLayer();
