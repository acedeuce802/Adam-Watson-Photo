/**
 * Cloudflare Worker backing the --paywall race galleries.
 *
 * Three routes, no npm dependencies (talks to Stripe/B2/Resend over plain
 * fetch, verifies Stripe's webhook signature with Web Crypto):
 *
 *   POST /checkout            { private_key, race } -> { url }
 *     Creates a Stripe Checkout Session with a dynamic price (no
 *     pre-created Stripe product needed per photo) and returns the
 *     Checkout URL for the browser to redirect to.
 *
 *   POST /webhook              (called by Stripe, not the browser)
 *     On checkout.session.completed: mints a time-limited B2 download
 *     authorization for the purchased photo and emails it to the buyer.
 *
 *   GET  /download?session_id= -> { url }
 *     Used by download.html right after Stripe redirects back. Verifies
 *     the session server-side (payment_status === 'paid') and mints the
 *     same kind of signed B2 URL, independent of whether the webhook has
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

  const { private_key: privateKey, race } = body || {};
  if (!privateKey || typeof privateKey !== 'string') {
    return jsonResponse({ error: 'Missing private_key' }, 400);
  }

  const priceCents = parseInt(env.PRICE_CENTS, 10);
  if (!Number.isFinite(priceCents) || priceCents <= 0) {
    return jsonResponse({ error: 'Server misconfigured: bad PRICE_CENTS' }, 500);
  }

  const productName = race ? `Full-resolution photo – ${race}` : 'Full-resolution photo';

  const params = new URLSearchParams({
    mode: 'payment',
    success_url: `${env.SITE_BASE_URL}/download.html?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${env.SITE_BASE_URL}/`,
    'line_items[0][quantity]': '1',
    'line_items[0][price_data][currency]': 'usd',
    'line_items[0][price_data][unit_amount]': String(priceCents),
    'line_items[0][price_data][product_data][name]': productName,
    'metadata[private_key]': privateKey,
    'metadata[race]': race || '',
  });

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

  const privateKey = session.metadata && session.metadata.private_key;
  if (!privateKey) {
    return jsonResponse({ error: 'No photo on this order' }, 404);
  }

  const downloadUrl = await mintB2DownloadUrl(privateKey, env);
  return jsonResponse({ url: downloadUrl });
}

// ---------------------------------------------------------------------------
// Fulfillment (webhook path)

async function fulfillOrder(session, env) {
  const privateKey = session.metadata && session.metadata.private_key;
  const email = session.customer_details && session.customer_details.email;

  if (!privateKey || !email) {
    console.error('Session missing private_key or buyer email', session.id);
    return;
  }

  const downloadUrl = await mintB2DownloadUrl(privateKey, env);
  await sendDownloadEmail(email, downloadUrl, env);
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
    }),
  });

  if (!authResp.ok) {
    throw new Error(`B2 get_download_authorization failed: ${await authResp.text()}`);
  }

  const { authorizationToken } = await authResp.json();
  const encodedFileName = fileName.split('/').map(encodeURIComponent).join('/');

  return `${auth.downloadUrl}/file/${env.B2_PRIVATE_BUCKET_NAME}/${encodedFileName}?Authorization=${authorizationToken}`;
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

async function sendDownloadEmail(toEmail, downloadUrl, env) {
  const resp = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: env.RESEND_FROM_EMAIL,
      to: toEmail,
      subject: 'Your full-resolution photo from Adam Watson Photo',
      html: `
        <p>Thanks for your purchase!</p>
        <p><a href="${downloadUrl}">Click here to download your full-resolution photo</a></p>
        <p>This link expires in about ${Math.round(
          parseInt(env.B2_DOWNLOAD_VALID_SECONDS || '172800', 10) / 3600
        )} hours.</p>
      `,
    }),
  });

  if (!resp.ok) {
    console.error('Resend send failed', await resp.text());
  }
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
