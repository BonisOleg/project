/**
 * Push GA4 purchase + Enhanced Conversions user_data once per transaction_id.
 * Anti-dupe: sessionStorage, cookie only as the same-id fallback.
 * LiqPay: poll until the backend marks the order paid.
 */

const STORAGE_PREFIX = 'oyra_ps_';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;
const POLL_INTERVAL_MS = 2000;
const POLL_LIMIT_MS = 90000;

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
    /* private mode / blocked — still allow one send via cookie check */
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

function pushOnce(payload) {
  const transactionId = payload?.ecommerce?.transaction_id;
  if (!transactionId || alreadySent(String(transactionId))) {
    return;
  }
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ ecommerce: null });
  window.dataLayer.push(payload);
  markSent(String(transactionId));
}

function delay(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function pollUntilPaid(url) {
  const started = Date.now();
  while (Date.now() - started <= POLL_LIMIT_MS) {
    try {
      const response = await fetch(url, {
        credentials: 'same-origin',
        cache: 'no-store',
        headers: { Accept: 'application/json' },
      });
      if (response.status === 404) {
        return;
      }
      if (response.ok) {
        const data = await response.json();
        if (data && data.ready && data.payload) {
          pushOnce(data.payload);
          return;
        }
      }
    } catch (_) {
      /* retry until the limit */
    }
    if (Date.now() - started > POLL_LIMIT_MS) {
      return;
    }
    await delay(POLL_INTERVAL_MS);
  }
}

export function initPurchaseDataLayer() {
  const node = document.getElementById('oyra-purchase-datalayer');
  if (node) {
    try {
      pushOnce(JSON.parse(node.textContent));
    } catch (_) {
      /* invalid payload */
    }
    return;
  }

  const poll = document.getElementById('oyra-purchase-poll');
  const url = poll && poll.dataset ? poll.dataset.url : '';
  if (!url) {
    return;
  }
  pollUntilPaid(url);
}

initPurchaseDataLayer();
