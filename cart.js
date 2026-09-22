/*
 * Shared shopping cart for paywalled galleries.
 *
 * One cart for the whole site: it lives in localStorage, so it follows a
 * visitor from album to album (and between tabs) and survives closing the
 * browser, for up to 30 days. Any page that loads this file gets the floating
 * cart bar and the cart review panel; paywalled galleries also use the
 * AWPCart API below to add/remove photos and start checkout.
 *
 * The purchase itself is handled by the Cloudflare Worker in worker/ (Stripe
 * Checkout). The price shown here comes from that Worker (GET /price), so it
 * always matches what Stripe will actually charge.
 */
(function () {
  'use strict';

  if (window.AWPCart) return;

  // Same Worker the checkout page and download.html talk to (worker/).
  var WORKER_BASE_URL = 'https://adam-watson-photo-paywall.adamwatsonphoto.workers.dev';

  var STORAGE_KEY = 'awp_cart_v1';
  var PRICE_KEY = 'awp_price_cents_v1';
  var PRICE_CHECKED_KEY = 'awp_price_checked_v1';
  var MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;      // carts older than this are dropped
  var PRICE_REFRESH_MS = 5 * 60 * 1000;           // re-ask the Worker for the price at most every 5 min
                                                   // (matches the Worker's own Cache-Control on /price,
                                                   // so this never asks more often than that response
                                                   // is actually fresh for anyway)
  var MAX_ITEMS = 100;                            // Stripe Checkout's limit per order
  // Only used until the Worker answers (or if it can't be reached); the real
  // price is whatever the Worker's PRICE_CENTS says.
  var FALLBACK_PRICE_CENTS = 1000;

  // ---- storage (falls back to memory if the browser blocks localStorage) ----

  var memoryStore = {};

  function read(key) {
    try { return window.localStorage.getItem(key); }
    catch (e) { return Object.prototype.hasOwnProperty.call(memoryStore, key) ? memoryStore[key] : null; }
  }

  function write(key, value) {
    try { window.localStorage.setItem(key, value); }
    catch (e) { memoryStore[key] = value; }
  }

  // ---- item validation (cart data lives in the browser, so treat it as untrusted) ----

  function cleanItem(raw) {
    if (!raw || typeof raw.key !== 'string' || !raw.key || raw.key.length > 300) return null;
    var page = typeof raw.page === 'string' && /^[\w.\-]+\.html$/.test(raw.page) ? raw.page : '';
    var thumb = typeof raw.thumb === 'string' && /^https:\/\//.test(raw.thumb) ? raw.thumb : '';
    var album = typeof raw.album === 'string' ? raw.album.slice(0, 80) : '';
    return { key: raw.key, album: album, page: page, thumb: thumb };
  }

  function loadItems() {
    try {
      var data = JSON.parse(read(STORAGE_KEY) || 'null');
      if (!data || !Array.isArray(data.items)) return [];
      if (Date.now() - (data.updated || 0) > MAX_AGE_MS) return [];
      var seen = {};
      return data.items.map(cleanItem).filter(function (item) {
        if (!item || seen[item.key]) return false;
        seen[item.key] = true;
        return true;
      });
    } catch (e) {
      return [];
    }
  }

  function loadPrice() {
    return parseInt(read(PRICE_KEY), 10) || FALLBACK_PRICE_CENTS;
  }

  var items = loadItems();
  var priceCents = loadPrice();
  var listeners = [];
  var pendingButton = null;   // checkout button currently showing "Redirecting..."

  function persist() {
    write(STORAGE_KEY, JSON.stringify({ updated: Date.now(), items: items }));
  }

  function indexOf(key) {
    for (var i = 0; i < items.length; i++) if (items[i].key === key) return i;
    return -1;
  }

  function changed() {
    persist();
    notify();
  }

  function notify() {
    render();
    listeners.slice().forEach(function (fn) {
      try { fn(); } catch (e) { console.error(e); }
    });
  }

  // ---- public API ----

  var api = {
    items: function () { return items.slice(); },
    count: function () { return items.length; },
    has: function (key) { return indexOf(key) !== -1; },

    add: function (raw) {
      var item = cleanItem(raw);
      if (!item) return false;
      if (indexOf(item.key) !== -1) return true;
      if (items.length >= MAX_ITEMS) {
        window.alert('A single order can include up to ' + MAX_ITEMS + ' photos. Check out this batch first, then add more.');
        return false;
      }
      items.push(item);
      changed();
      return true;
    },

    remove: function (key) { return api.removeMany([key]); },

    removeMany: function (keys) {
      var before = items.length;
      items = items.filter(function (item) { return keys.indexOf(item.key) === -1; });
      if (items.length !== before) changed();
      return before - items.length;
    },

    // Returns true if the photo is in the cart afterwards.
    toggle: function (raw) {
      var item = cleanItem(raw);
      if (!item) return false;
      if (indexOf(item.key) !== -1) { api.remove(item.key); return false; }
      return api.add(item);
    },

    clear: function () {
      if (!items.length) return;
      items = [];
      changed();
    },

    price: function () { return priceCents; },
    totalCents: function () { return items.length * priceCents; },
    formatPrice: function (cents) { return '$' + (cents / 100).toFixed(2); },
    onChange: function (fn) { listeners.push(fn); },

    // Ask the Worker for the current per-photo price (at most every PRICE_REFRESH_MS).
    refreshPrice: function () {
      var checked = parseInt(read(PRICE_CHECKED_KEY), 10) || 0;
      if (Date.now() - checked < PRICE_REFRESH_MS) return;
      fetch(WORKER_BASE_URL + '/price')
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data || !(data.price_cents > 0)) return;
          write(PRICE_CHECKED_KEY, String(Date.now()));
          if (data.price_cents !== priceCents) {
            priceCents = data.price_cents;
            write(PRICE_KEY, String(priceCents));
            notify();
          }
        })
        .catch(function () { /* keep the cached/fallback price */ });
    },

    // Start Stripe Checkout for `list` (default: everything in the cart).
    // Deliberately does NOT touch the cart: it is cleared on the success page,
    // so backing out of checkout leaves everything where it was.
    checkout: function (list, buttonEl, resetLabel) {
      list = list || items;
      if (!list.length) return Promise.resolve();

      if (buttonEl) {
        buttonEl.disabled = true;
        buttonEl.textContent = 'Redirecting to checkout...';
        pendingButton = { el: buttonEl, label: resetLabel };
      }

      return fetch(WORKER_BASE_URL + '/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: list.map(function (item) { return { private_key: item.key, album: item.album || '' }; }),
          return_url: window.location.href.split('#')[0]
        })
      })
        .then(function (response) {
          if (!response.ok) throw new Error('Checkout request failed (' + response.status + ')');
          return response.json();
        })
        .then(function (data) {
          if (!data.url) throw new Error('No checkout URL returned');
          window.location.href = data.url;
        })
        .catch(function (error) {
          console.error('Checkout failed:', error);
          window.alert('Sorry, checkout could not be started. Please try again in a moment.');
          resetPending();
        });
    }
  };

  function resetPending() {
    if (!pendingButton) return;
    pendingButton.el.disabled = false;
    pendingButton.el.textContent = pendingButton.label;
    pendingButton = null;
  }

  window.AWPCart = api;

  // Coming back from Stripe with the browser's Back button can restore this page
  // exactly as it was left ("Redirecting..." and all), so undo that.
  window.addEventListener('pageshow', function (event) {
    if (event.persisted) { resetPending(); items = loadItems(); notify(); }
  });

  // Keep every open tab in sync.
  window.addEventListener('storage', function (event) {
    if (event.key === STORAGE_KEY || event.key === PRICE_KEY) {
      items = loadItems();
      priceCents = loadPrice();
      notify();
    }
  });

  // ---- UI: floating bar + review panel (built here so any page can use it) ----

  var CSS = [
    '.awp-cart-bar{position:fixed;right:30px;bottom:30px;z-index:9000;display:flex;align-items:center;gap:12px;',
    'background:rgba(15,15,15,.95);border:1px solid #d4a017;border-radius:25px;padding:8px 8px 8px 20px;',
    'box-shadow:0 4px 20px rgba(0,0,0,.5);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}',
    '.awp-cart-bar[hidden]{display:none}',
    '.awp-cart-summary{background:none;border:0;color:#e0e0e0;font:inherit;font-size:.95em;cursor:pointer;padding:0;white-space:nowrap}',
    '.awp-cart-summary:hover{color:#fff;text-decoration:underline}',
    '.awp-cart-bar .awp-btn{font:inherit;font-size:.95em;border-radius:20px;padding:8px 18px;cursor:pointer;border:0;white-space:nowrap}',
    '.awp-btn-gold{background:#d4a017;color:#1a1a1a;font-weight:600}',
    '.awp-btn-gold:disabled{opacity:.6;cursor:wait}',
    '.awp-btn-ghost{background:transparent;color:#aaa;border:1px solid #555!important}',
    '.awp-btn-ghost:hover{color:#fff;border-color:#999!important}',
    '.awp-cart-panel{position:fixed;inset:0;z-index:9500;display:flex;align-items:center;justify-content:center;',
    'background:rgba(0,0,0,.7);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}',
    '.awp-cart-panel[hidden]{display:none}',
    '.awp-cart-sheet{background:#141414;color:#e0e0e0;border:1px solid #333;border-radius:12px;width:min(560px,92vw);',
    'max-height:82vh;display:flex;flex-direction:column;box-shadow:0 10px 40px rgba(0,0,0,.6)}',
    '.awp-cart-head{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid #2a2a2a}',
    '.awp-cart-head h2{font-size:1.15em;font-weight:400;color:#fff;margin:0;letter-spacing:.5px}',
    '.awp-cart-x{background:none;border:0;color:#aaa;font-size:1.8em;line-height:1;cursor:pointer;padding:0 4px}',
    '.awp-cart-x:hover{color:#fff}',
    '.awp-cart-list{overflow-y:auto;padding:6px 20px 12px}',
    '.awp-cart-album{margin:14px 0 6px;font-size:.85em;letter-spacing:1px;text-transform:uppercase;color:#888}',
    '.awp-cart-album a{color:#d4a017;text-decoration:none}',
    '.awp-cart-album a:hover{text-decoration:underline}',
    '.awp-cart-row{display:flex;align-items:center;gap:12px;padding:6px 0}',
    '.awp-cart-thumb{width:64px;height:48px;object-fit:cover;border-radius:4px;background:#2a2a2a;flex-shrink:0}',
    '.awp-cart-name{flex:1;min-width:0;font-size:.9em;color:#ccc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
    '.awp-cart-remove{background:none;border:1px solid #444;color:#aaa;border-radius:14px;font:inherit;font-size:.8em;padding:4px 10px;cursor:pointer}',
    '.awp-cart-remove:hover{color:#fff;border-color:#999}',
    '.awp-cart-foot{display:flex;align-items:center;gap:10px;padding:14px 20px;border-top:1px solid #2a2a2a}',
    '.awp-cart-total{flex:1;font-size:1.05em;color:#fff}',
    '.awp-cart-foot .awp-btn{font:inherit;font-size:.95em;border-radius:20px;padding:9px 20px;cursor:pointer;border:0}',
    '@media (max-width:640px){',
    '.awp-cart-bar{left:20px;right:20px;justify-content:space-between}',
    '.awp-cart-panel{align-items:flex-end}',
    '.awp-cart-sheet{width:100%;max-height:88vh;border-radius:16px 16px 0 0;border-bottom:0}',
    '.awp-cart-foot{flex-wrap:wrap}',
    '.awp-cart-total{flex-basis:100%}',
    '.awp-cart-foot .awp-btn{flex:1}',
    '}'
  ].join('');

  var ui = null;

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function buildUI() {
    var style = el('style');
    style.textContent = CSS;
    document.head.appendChild(style);

    var bar = el('div', 'awp-cart-bar');
    bar.hidden = true;
    var summary = el('button', 'awp-cart-summary');
    summary.type = 'button';
    summary.setAttribute('aria-haspopup', 'dialog');
    summary.title = 'Review your cart';
    var barCheckout = el('button', 'awp-btn awp-btn-gold', 'Checkout');
    barCheckout.type = 'button';
    bar.appendChild(summary);
    bar.appendChild(barCheckout);

    var panel = el('div', 'awp-cart-panel');
    panel.hidden = true;
    var sheet = el('div', 'awp-cart-sheet');
    sheet.setAttribute('role', 'dialog');
    sheet.setAttribute('aria-modal', 'true');
    sheet.setAttribute('aria-label', 'Your cart');
    var head = el('div', 'awp-cart-head');
    var title = el('h2', '', 'Your cart');
    var close = el('button', 'awp-cart-x', '×');
    close.type = 'button';
    close.setAttribute('aria-label', 'Close cart');
    head.appendChild(title);
    head.appendChild(close);
    var list = el('div', 'awp-cart-list');
    var foot = el('div', 'awp-cart-foot');
    var total = el('div', 'awp-cart-total');
    var clearBtn = el('button', 'awp-btn awp-btn-ghost', 'Clear cart');
    clearBtn.type = 'button';
    var panelCheckout = el('button', 'awp-btn awp-btn-gold', 'Checkout');
    panelCheckout.type = 'button';
    foot.appendChild(total);
    foot.appendChild(clearBtn);
    foot.appendChild(panelCheckout);
    sheet.appendChild(head);
    sheet.appendChild(list);
    sheet.appendChild(foot);
    panel.appendChild(sheet);

    document.body.appendChild(bar);
    document.body.appendChild(panel);

    summary.addEventListener('click', openPanel);
    close.addEventListener('click', closePanel);
    panel.addEventListener('click', function (e) { if (e.target === panel) closePanel(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !panel.hidden) closePanel(); });
    barCheckout.addEventListener('click', function () { api.checkout(null, barCheckout, 'Checkout'); });
    panelCheckout.addEventListener('click', function () { api.checkout(null, panelCheckout, 'Checkout'); });
    clearBtn.addEventListener('click', function () { api.clear(); });

    ui = { bar: bar, summary: summary, panel: panel, list: list, total: total, close: close };
    return ui;
  }

  function openPanel() {
    if (!ui) return;
    ui.panel.hidden = false;
    renderPanel();
    ui.close.focus();
    api.refreshPrice();
  }

  function closePanel() {
    if (ui) ui.panel.hidden = true;
  }

  function filenameOf(item) {
    return item.key.split('/').pop();
  }

  function renderPanel() {
    ui.list.textContent = '';

    var groups = [];
    var byAlbum = {};
    items.forEach(function (item) {
      var groupKey = item.page || item.album || 'Photos';   // one group per album page
      if (!byAlbum[groupKey]) {
        byAlbum[groupKey] = { name: item.album || 'Photos', page: item.page, items: [] };
        groups.push(byAlbum[groupKey]);
      }
      byAlbum[groupKey].items.push(item);
    });

    groups.forEach(function (group) {
      var heading = el('div', 'awp-cart-album');
      if (group.page) {
        var link = el('a', '', group.name);
        link.href = group.page;
        heading.appendChild(link);
      } else {
        heading.textContent = group.name;
      }
      ui.list.appendChild(heading);

      group.items.forEach(function (item) {
        var row = el('div', 'awp-cart-row');
        var thumb = el('img', 'awp-cart-thumb');
        thumb.alt = '';
        if (item.thumb) thumb.src = item.thumb;
        var name = el('div', 'awp-cart-name', filenameOf(item));
        var remove = el('button', 'awp-cart-remove', 'Remove');
        remove.type = 'button';
        remove.addEventListener('click', function () { api.remove(item.key); });
        row.appendChild(thumb);
        row.appendChild(name);
        row.appendChild(remove);
        ui.list.appendChild(row);
      });
    });
  }

  function render() {
    if (!document.body) return;
    if (!ui) {
      if (items.length === 0) return;   // nothing to show: don't touch the page at all
      buildUI();
    }

    var n = items.length;
    ui.bar.hidden = n === 0;
    ui.summary.textContent = n + ' photo' + (n === 1 ? '' : 's') + ' · ' + api.formatPrice(api.totalCents());

    if (n === 0) {
      closePanel();
    } else if (!ui.panel.hidden) {
      renderPanel();
    }
    ui.total.textContent = n + ' photo' + (n === 1 ? '' : 's') + ' · ' + api.formatPrice(api.totalCents());
  }

  if (document.body) render();
  else document.addEventListener('DOMContentLoaded', render);
})();
