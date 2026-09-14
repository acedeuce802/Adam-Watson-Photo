# Paywall Worker

Small Cloudflare Worker that backs the `--paywall` race galleries generated
by `../Scripts/generate_gallery.py`. It has no build step and no npm
dependencies -- `src/index.js` talks to Stripe, Backblaze B2, and Resend
directly over `fetch`.

Ships on the free `*.workers.dev` subdomain, so no DNS changes to
adamwatsonphoto.com are required. The Worker sends CORS headers allowing
requests from `https://adamwatsonphoto.com` (see `ALLOWED_ORIGIN` in
`wrangler.toml`).

## One-time account setup

1. **Backblaze B2** -- you already have the private bucket. In the B2
   console, go to *App Keys -> Add a New Application Key*:
   - **Allow access to Bucket(s)**: pick your private bucket specifically
     (not "All"). This is what matters most -- scoping the key to one bucket
     makes B2's authorize-account response name that bucket's ID directly,
     so the Worker never needs a second API call to look it up.
   - **Type of Access**: "Read Only" is sufficient (it includes the
     `shareFiles` capability the Worker needs to mint time-limited download
     links, alongside `listFiles`/`readFiles`). Don't grant write/delete --
     the Worker never uploads or removes anything.
   - Click *Create New Key*. B2 shows the **keyID** and **applicationKey**
     exactly once -- copy both somewhere safe immediately (a password
     manager, not this chat). If you lose them you just make a new key.
   - These two values go straight into `wrangler secret put` below -- you
     paste them into your own terminal, I never see them.

2. **Stripe** -- sign up at stripe.com. Nothing special to configure:
   - Every new account starts in **test mode**, which works immediately with
     no business verification, no bank account, and fake card numbers --
     that's what we use for everything below until you're ready to take real
     money.
   - Grab the test **secret key** (starts `sk_test_...`) from
     *Developers -> API keys*.
   - You do **not** need to pre-create a "Product" or "Price" for each photo
     in the Stripe dashboard -- the Worker creates a one-off price on the fly
     for every checkout (`price_data` in `handleCheckout`), which is what
     makes a flat per-photo fee work without any per-race Stripe setup.
   - You'll add the webhook endpoint after the first deploy (step 5 below),
     since it needs the deployed Worker URL.
   - When you're ready to accept real payments: flip the dashboard's toggle
     from test to **live mode**, finish Stripe's business/bank verification
     (a short form -- this is Stripe confirming who gets paid out, not
     anything you need our infra for), grab the *live* secret key, and redo
     the webhook step in live mode. Test and live are entirely separate API
     keys/webhooks/data, so nothing in test mode risks a real charge.

3. **Resend** -- this is the email-sending piece. Cloudflare Workers can't
   run its own mail server (and even if it could, a brand-new sending IP
   gets flagged as spam), so Resend is a small transactional-email API: the
   Worker POSTs `{ to, subject, html }` to it and Resend handles actual
   delivery/reputation. Free tier (100 emails/day) is far more than you'll
   need for per-photo sales.
   - Sign up at resend.com.
   - For quick testing, you can send from their sandbox address without any
     setup, but it only delivers to *your own* Resend account email.
   - To actually email buyers, verify a sending domain: *Domains -> Add
     Domain* in Resend, use something like `mail.adamwatsonphoto.com` (a
     subdomain keeps this separate from your site's own DNS records), and
     add the SPF/DKIM records Resend gives you. Since your domain is already
     on Cloudflare, add them under *DNS* in the Cloudflare dashboard for
     adamwatsonphoto.com -- same zone, just a couple of new TXT/CNAME rows.
     Verification is usually near-instant once the records are added.
   - Grab the **API key** from *API Keys* in Resend once you're set up.

4. **Cloudflare Workers** -- you already have a Cloudflare account for the
   domain's DNS, which is exactly the account this uses too; nothing new to
   sign up for. `wrangler` is Cloudflare's separate CLI tool for *deploying
   code* (Workers), distinct from the DNS dashboard you already use:
   ```bash
   npm install -g wrangler   # needs Node.js installed; nodejs.org if you don't have it
   wrangler login            # opens a browser tab to authorize the CLI against your existing Cloudflare account
   ```
   `wrangler login` is a one-time device authorization, like logging into
   the dashboard but for command-line deploys -- it doesn't touch or need
   your domain's DNS records at all, since the Worker ships on Cloudflare's
   free `*.workers.dev` subdomain instead (see below).

## Deploy

From this `worker/` directory:

```bash
wrangler secret put STRIPE_SECRET_KEY
wrangler secret put STRIPE_WEBHOOK_SECRET
wrangler secret put B2_KEY_ID
wrangler secret put B2_APP_KEY
wrangler secret put RESEND_API_KEY
wrangler secret put PRICE_CENTS
```

- `PRICE_CENTS` is the flat per-photo price, e.g. `1000` for $10.00.
- `STRIPE_WEBHOOK_SECRET` doesn't exist yet on your very first deploy --
  put in any placeholder value, deploy once to get your `*.workers.dev` URL,
  add the webhook in Stripe (below), then run
  `wrangler secret put STRIPE_WEBHOOK_SECRET` again with the real value and
  redeploy.

Non-secret config lives in `wrangler.toml` (`ALLOWED_ORIGIN`,
`SITE_BASE_URL`, `B2_PRIVATE_BUCKET_NAME`, `B2_DOWNLOAD_VALID_SECONDS`,
`RESEND_FROM_EMAIL`) -- edit those directly if they need to change.

```bash
wrangler deploy
```

`wrangler deploy` uploads `src/index.js` and runs it on Cloudflare's edge --
this is the actual "publish the backend" step, separate from and unrelated
to your site's DNS. It prints a URL on Cloudflare's free `workers.dev`
subdomain (not `adamwatsonphoto.com`), so this never touches your domain's
DNS zone. You re-run this same command any time you change `src/index.js`.

Take the printed `https://adam-watson-photo-paywall.<your-subdomain>.workers.dev`
URL and paste it into:
- `_WORKER_BASE_URL` near the top of `../Scripts/generate_gallery.py`
- `WORKER_BASE_URL` in `../download.html`

Then regenerate any `--paywall` galleries so they call the real URL.

## Wire up the Stripe webhook

In the Stripe dashboard: *Developers -> Webhooks -> Add endpoint*.
- Endpoint URL: `https://<your-worker>.workers.dev/webhook`
- Events to send: `checkout.session.completed`

Copy the **signing secret** Stripe shows you and set it:
```bash
wrangler secret put STRIPE_WEBHOOK_SECRET
wrangler deploy
```

## Testing end-to-end (Stripe test mode)

1. `wrangler tail` in one terminal to watch live logs.
2. Open a `--paywall` gallery, open the lightbox, click **Buy Full-Res**.
3. On the Stripe Checkout page, pay with the test card `4242 4242 4242 4242`,
   any future expiry, any CVC, any email you can actually check.
4. You should land on `download.html` with a working download link almost
   immediately (via `GET /download`), and `wrangler tail` should show the
   `/webhook` request landing shortly after with a `checkout.session.completed`
   event. Check that the email arrives too.
5. Confirm the download link actually serves the true full-resolution file,
   and that it stops working after `B2_DOWNLOAD_VALID_SECONDS` has passed.

Once that all works in test mode, switch to Stripe's live API keys
(`wrangler secret put STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` with the
live-mode values, and re-add the webhook endpoint in live mode) to start
taking real payments.
