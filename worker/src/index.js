/**
 * Cloudflare Worker backing the --paywall race galleries.
 *
 * Three routes, no npm dependencies (talks to Stripe/B2/Resend over plain
 * fetch, verifies Stripe's webhook signature with Web Crypto):
 *
 *   POST /checkout            { private_keys: [...], race } -> { url }
 *     Creates ONE Stripe Checkout Session with one line item per photo
 *     (dynamic price, no pre-created Stripe product needed) and returns
 *     the Checkout URL for the browser to redirect to -- covers both an
 *     instant single-photo buy (array of one) and a cart checkout (array
 *     of many) the same way. `private_key` (singular) is still accepted
 *     for backward compatibility with any already-generated gallery page.
 *
 *   POST /webhook              (called by Stripe, not the browser)
 *     On checkout.session.completed: mints a time-limited B2 download
 *     authorization for every purchased photo and emails the buyer the
 *     full list.
 *
 *   GET  /download?session_id= -> { downloads: [{filename, url}, ...] }
 *     Used by download.html right after Stripe redirects back. Verifies
 *     the session server-side (payment_status === 'paid') and mints the
 *     same kind of signed B2 URLs, independent of whether the webhook has
 *     already run.
 *
 * See ../README.md for the required secrets and deploy steps.
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return withCors(env, new Response(null, { status: 204 }));
    }

    try {
      if (url.pathname === '/checkout' && request.method === 'POST') {
        return withCors(env, await handleCheckout(request, env));
      }
      if (url.pathname === '/webhook' && request.method === 'POST') {
        return await handleWebhook(request, env);
      }
      if (url.pathname === '/download' && request.method === 'GET') {
        return withCors(env, await handleDownload(url, env));
      }
      return withCors(env, jsonResponse({ error: 'Not found' }, 404));
    } catch (err) {
      console.error(err);
      return withCors(env, jsonResponse({ error: 'Internal error' }, 500));
    }
  },
};

// ---------------------------------------------------------------------------
// Routes

async function handleCheckout(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ error: 'Invalid JSON body' }, 400);
  }

  let privateKeys = body && body.private_keys;
  if (!Array.isArray(privateKeys) && body && typeof body.private_key === 'string') {
    privateKeys = [body.private_key]; // backward compat: older gallery pages send one key
  }
  if (!Array.isArray(privateKeys)) privateKeys = [];
  privateKeys = [...new Set(privateKeys.filter((k) => typeof k === 'string' && k))];

  if (privateKeys.length === 0) {
    return jsonResponse({ error: 'Missing private_keys' }, 400);
  }

  const priceCents = parseInt(env.PRICE_CENTS, 10);
  if (!Number.isFinite(priceCents) || priceCents <= 0) {
    return jsonResponse({ error: 'Server misconfigured: bad PRICE_CENTS' }, 500);
  }

  const race = body.race || '';

  const params = new URLSearchParams({
    mode: 'payment',
    success_url: `${env.SITE_BASE_URL}/download.html?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${env.SITE_BASE_URL}/`,
  });

  privateKeys.forEach((key, i) => {
    const filename = key.split('/').pop();
    const productName = race ? `Full-resolution photo – ${filename} (${race})` : `Full-resolution photo – ${filename}`;
    params.set(`line_items[${i}][quantity]`, '1');
    params.set(`line_items[${i}][price_data][currency]`, 'usd');
    params.set(`line_items[${i}][price_data][unit_amount]`, String(priceCents));
    params.set(`line_items[${i}][price_data][product_data][name]`, productName);
  });

  params.set('metadata[race]', race);
  for (const [key, value] of Object.entries(encodePrivateKeysToMetadata(privateKeys))) {
    params.set(`metadata[${key}]`, value);
  }

  const resp = await fetch('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params.toString(),
  });

  const data = await resp.json();
  if (!resp.ok) {
    console.error('Stripe checkout.sessions.create failed', data);
    return jsonResponse({ error: 'Could not create checkout session' }, 502);
  }

  return jsonResponse({ url: data.url });
}

async function handleWebhook(request, env) {
  const payload = await request.text();
  const signatureHeader = request.headers.get('Stripe-Signature') || '';

  const valid = await verifyStripeSignature(payload, signatureHeader, env.STRIPE_WEBHOOK_SECRET);
  if (!valid) {
    return new Response('Invalid signature', { status: 400 });
  }

  const event = JSON.parse(payload);

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;
    try {
      await fulfillOrder(session, env);
    } catch (err) {
      // Returning 500 makes Stripe retry the webhook later -- useful if B2
      // or Resend is briefly down, since the buyer already paid.
      console.error('fulfillOrder failed', err);
      return new Response('Fulfillment error', { status: 500 });
    }
  }

  return new Response('ok', { status: 200 });
}

async function handleDownload(url, env) {
  const sessionId = url.searchParams.get('session_id');
  if (!sessionId) {
    return jsonResponse({ error: 'Missing session_id' }, 400);
  }

  const resp = await fetch(
    `https://api.stripe.com/v1/checkout/sessions/${encodeURIComponent(sessionId)}`,
    { headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` } }
  );
  const session = await resp.json();

  if (!resp.ok) {
    console.error('Stripe checkout.sessions.retrieve failed', session);
    return jsonResponse({ error: 'Order not found' }, 404);
  }
  if (session.payment_status !== 'paid') {
    return jsonResponse({ error: 'Payment not confirmed yet' }, 402);
  }

  const privateKeys = decodePrivateKeysFromMetadata(session.metadata || {});
  if (privateKeys.length === 0) {
    return jsonResponse({ error: 'No photos on this order' }, 404);
  }

  const downloads = await mintDownloads(privateKeys, env);
  return jsonResponse({ downloads });
}

// ---------------------------------------------------------------------------
// Fulfillment (webhook path)

async function fulfillOrder(session, env) {
  const privateKeys = decodePrivateKeysFromMetadata(session.metadata || {});
  const email = session.customer_details && session.customer_details.email;

  if (privateKeys.length === 0 || !email) {
    console.error('Session missing private_keys or buyer email', session.id);
    return;
  }

  const downloads = await mintDownloads(privateKeys, env);
  await sendDownloadEmail(email, downloads, env);
}

async function mintDownloads(privateKeys, env) {
  return Promise.all(
    privateKeys.map(async (key) => ({
      filename: key.split('/').pop(),
      url: await mintB2DownloadUrl(key, env),
    }))
  );
}

// ---------------------------------------------------------------------------
// Stripe metadata encoding for a cart's worth of private keys
//
// Session metadata values are capped at 500 bytes each (and 50 keys total),
// so a cart's private_key list is JSON-encoded in chunks small enough to
// stay well under that per-value limit, spread across metadata fields
// private_keys_0, private_keys_1, etc. That comfortably covers even a very
// large cart. metadata.private_key (singular) is still read as a fallback
// for any session created before this went in.

function encodePrivateKeysToMetadata(privateKeys) {
  const chunks = [];
  let current = [];
  let currentLength = 2; // "[]"

  for (const key of privateKeys) {
    const entryLength = JSON.stringify(key).length + 1; // +1 for the comma
    if (current.length > 0 && currentLength + entryLength > 450) {
      chunks.push(current);
      current = [];
      currentLength = 2;
    }
    current.push(key);
    currentLength += entryLength;
  }
  if (current.length > 0) chunks.push(current);

  const metadata = { private_keys_chunks: String(chunks.length) };
  chunks.forEach((chunk, i) => {
    metadata[`private_keys_${i}`] = JSON.stringify(chunk);
  });
  return metadata;
}

function decodePrivateKeysFromMetadata(metadata) {
  const chunkCount = parseInt(metadata.private_keys_chunks || '0', 10);
  let keys = [];

  for (let i = 0; i < chunkCount; i++) {
    const raw = metadata[`private_keys_${i}`];
    if (!raw) continue;
    try {
      keys = keys.concat(JSON.parse(raw));
    } catch (err) {
      console.error(`Could not parse private_keys_${i} metadata chunk`, raw);
    }
  }

  if (keys.length === 0 && metadata.private_key) {
    keys = [metadata.private_key]; // backward compat with pre-cart sessions
  }

  return keys;
}

// ---------------------------------------------------------------------------
// Backblaze B2 (private bucket, signed download URLs)
//
// The B2 application key MUST be scoped to only the private bucket -- that
// makes B2's account-authorize response name the bucket's ID directly
// (`allowed.bucketId`), so this never needs a separate bucket lookup.

async function mintB2DownloadUrl(fileName, env) {
  const auth = await b2Authorize(env);
  const bucketId = auth.allowed && auth.allowed.bucketId;
  if (!bucketId) {
    throw new Error(
      'B2 application key is not scoped to a single bucket (allowed.bucketId missing)'
    );
  }

  const validSeconds = parseInt(env.B2_DOWNLOAD_VALID_SECONDS || '172800', 10);

  // Ask B2 to serve this file with Content-Disposition: attachment, so the
  // browser downloads it directly instead of navigating to/opening it --
  // a plain HTML `download` attribute can't force that for a cross-origin
  // URL like this one, so it has to come from B2 as a response header.
  const downloadFilename = fileName.split('/').pop().replace(/"/g, '');
  const contentDisposition = `attachment; filename="${downloadFilename}"`;

  const authResp = await fetch(`${auth.apiUrl}/b2api/v2/b2_get_download_authorization`, {
    method: 'POST',
    headers: {
      Authorization: auth.authorizationToken,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      bucketId,
      fileNamePrefix: fileName,
      validDurationInSeconds: validSeconds,
      b2ContentDisposition: contentDisposition,
    }),
  });

  if (!authResp.ok) {
    throw new Error(`B2 get_download_authorization failed: ${await authResp.text()}`);
  }

  const { authorizationToken } = await authResp.json();
  const encodedFileName = fileName.split('/').map(encodeURIComponent).join('/');
  const params = new URLSearchParams({
    Authorization: authorizationToken,
    b2ContentDisposition: contentDisposition,
  });

  return `${auth.downloadUrl}/file/${env.B2_PRIVATE_BUCKET_NAME}/${encodedFileName}?${params.toString()}`;
}

async function b2Authorize(env) {
  const credentials = btoa(`${env.B2_KEY_ID}:${env.B2_APP_KEY}`);
  const resp = await fetch('https://api.backblazeb2.com/b2api/v2/b2_authorize_account', {
    headers: { Authorization: `Basic ${credentials}` },
  });
  if (!resp.ok) {
    throw new Error(`B2 authorize_account failed: ${await resp.text()}`);
  }
  return resp.json();
}

// ---------------------------------------------------------------------------
// Email (Resend)

async function sendDownloadEmail(toEmail, downloads, env) {
  const plural = downloads.length > 1;
  const subject = plural
    ? `Your ${downloads.length} full-resolution photos from Adam Watson Photo`
    : 'Your full-resolution photo from Adam Watson Photo';
  const linksHtml = downloads
    .map((d) => `<p><a href="${d.url}">${escapeHtml(d.filename)}</a></p>`)
    .join('');
  const expiresHours = Math.round(parseInt(env.B2_DOWNLOAD_VALID_SECONDS || '172800', 10) / 3600);
  const supportEmail = env.SUPPORT_EMAIL;

  const resp = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: env.RESEND_FROM_EMAIL,
      to: toEmail,
      reply_to: supportEmail,
      subject,
      html: `
        <p>Thanks for your purchase! Click below to download your full-resolution photo${plural ? 's' : ''}:</p>
        ${linksHtml}
        <p>These links expire in about ${expiresHours} hours. If they expire before you get to them, just forward
        this email to <a href="mailto:${supportEmail}">${supportEmail}</a> as proof of purchase and I'll send
        the photos directly.</p>
        <p>Thank you!<br>Adam Watson</p>
      `,
    }),
  });

  if (!resp.ok) {
    console.error('Resend send failed', await resp.text());
  }
}

function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c]);
}

// ---------------------------------------------------------------------------
// Stripe webhook signature verification (HMAC-SHA256 via Web Crypto)

async function verifyStripeSignature(payload, signatureHeader, secret) {
  if (!signatureHeader) return false;

  const parts = Object.fromEntries(
    signatureHeader.split(',').map((kv) => {
      const [k, v] = kv.split('=');
      return [k, v];
    })
  );
  const timestamp = parts.t;
  const signature = parts.v1;
  if (!timestamp || !signature) return false;

  // Reject old timestamps to guard against replay of a captured payload.
  const ageSeconds = Math.abs(Date.now() / 1000 - Number(timestamp));
  if (!Number.isFinite(ageSeconds) || ageSeconds > 300) return false;

  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const signedPayload = `${timestamp}.${payload}`;
  const sigBuffer = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(signedPayload));
  const expected = [...new Uint8Array(sigBuffer)]
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  return timingSafeEqual(expected, signature);
}

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}

// ---------------------------------------------------------------------------
// Helpers

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function withCors(env, response) {
  const headers = new Headers(response.headers);
  headers.set('Access-Control-Allow-Origin', env.ALLOWED_ORIGIN);
  headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  headers.set('Access-Control-Allow-Headers', 'Content-Type');
  return new Response(response.body, { status: response.status, headers });
}
