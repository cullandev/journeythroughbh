# Journey Through Behavioral Health — website

A small, fast, private website for a therapy practice. Plain HTML, CSS, and a little
JavaScript, hosted on **Cloudflare Workers (static assets)** with one Worker route that
handles the contact form.

- Design plan: [DESIGN.md](DESIGN.md)
- Cloudflare setup, step by step: [docs/CLOUDFLARE-SETUP.md](docs/CLOUDFLARE-SETUP.md)
- No cookies, no analytics, no third-party fonts or embeds. **No cookie banner is needed**
  because the site sets no cookies and loads nothing that does. The only external request
  is Cloudflare Turnstile, on the Contact page only, to stop form spam.

## Layout

```
/
├── public/                  # the deployed site, served as static assets
│   ├── *.html               # GENERATED from src/pages by scripts/build.py (committed)
│   ├── css/site.css
│   ├── js/nav.js, faq.js, contact.js
│   ├── fonts/               # self-hosted fonts (TODO: add files, see fonts/README.md)
│   ├── images/
│   ├── _headers             # security headers for static responses
│   ├── robots.txt, sitemap.xml, 404.html
├── src/
│   ├── worker.js            # POST /api/contact; everything else -> static assets
│   └── pages/*.html         # page content + front matter (edit these, not public/*.html)
├── scripts/
│   ├── build.py             # stitches shared header/footer around each page
│   └── preview.py           # no-Node local preview (see below)
├── wrangler.jsonc
├── package.json
└── README.md
```

### Why there is a (tiny) generator

Twelve pages share the same header, nav, and footer. Rather than paste them twelve times,
`scripts/build.py` wraps each file in `src/pages/` with the shared chrome and writes the
result to `public/`. The output is committed, so **deploying needs no build step** and
Workers Builds just runs `wrangler deploy`. If you edit a page:

```bash
python scripts/build.py
```

`python scripts/build.py --check` fails if `public/` is out of date (handy in CI or a
pre-commit hook). Python 3.8+ with no extra packages.

## Local development

Two options.

**Full (recommended):** runs the real Worker, Turnstile verification, and email binding.

```bash
npm install
cp .dev.vars.example .dev.vars   # test Turnstile secret, your CONTACT_TO
npm run dev                      # http://localhost:8787
```

With the test keys in `.dev.vars` and in `contact.html`, the Turnstile check always passes
locally. Emails are simulated (logged) by `wrangler dev` unless you add `"remote": true` to
the `send_email` binding in `wrangler.jsonc`.

**Quick (no Node):** serves `public/` with the same URL handling and a fake `/api/contact`
that always succeeds. Good for checking copy and layout.

```bash
python scripts/preview.py        # http://localhost:8788
```

## Deploying with Workers Builds

1. Push this repository to GitHub.
2. In the Cloudflare dashboard go to **Compute & AI → Workers & Pages → Create → Import a
   repository**, pick this repo, and accept the defaults. Build command: leave empty (or
   `npm install`); deploy command: `npx wrangler deploy`.
3. Every push to `main` deploys to production. Enable **non-production branch builds** in
   the Worker's Builds settings so pull requests get preview URLs (`preview_urls` is already
   on in `wrangler.jsonc`).

### Custom domain

In the Worker's **Settings → Domains & Routes**, add `journeythroughbh.com` and
`www.journeythroughbh.com` as custom domains. The domain must be on Cloudflare DNS.
Then update `SITE` in `scripts/build.py` if the domain differs, rebuild, and commit.

### Secrets and variables

```bash
npx wrangler secret put TURNSTILE_SECRET
```

Non-secret values live in `wrangler.jsonc` under `vars` and can also be edited in the
dashboard under **Settings → Variables**:

| Variable              | Purpose                                                   |
|-----------------------|-----------------------------------------------------------|
| `CONTACT_TO`          | Where contact-form messages are delivered. **TODO**       |
| `CONTACT_FROM`        | Sender address on your onboarded Email Service domain     |
| `TURNSTILE_HOSTNAMES` | Comma-separated hostnames the form may be submitted from  |

### Email delivery (Cloudflare Email Service)

The Worker sends through the `EMAIL` binding (Cloudflare Email Service). Sending to a
*verified destination address* in your account is free on every plan; sending anywhere
else needs Workers Paid.
Setup:

1. Dashboard → **Compute & AI → Email Service → Onboard domain** → choose
   `journeythroughbh.com` and add the SPF/DKIM records it gives you.
2. Make sure `CONTACT_FROM` uses that domain and `CONTACT_TO` is the inbox that should
   receive inquiries. If `CONTACT_TO` is on a different domain, no extra setup is needed.

If you'd rather use Resend or another provider, replace the `env.EMAIL.send(...)` block in
`src/worker.js` with that provider's API call, store its key with
`wrangler secret put RESEND_API_KEY`, and remove the `send_email` binding.

### Turnstile

1. Dashboard → **Turnstile → Add widget**. Hostname: `journeythroughbh.com` (add the
   `workers.dev` preview hostname too if you want the form working on previews). Widget
   mode: Managed.
2. Put the **site key** in `src/pages/contact.html` (replace the `1x0000…AA` test key),
   run `python scripts/build.py`, commit.
3. Put the **secret key** in the Worker: `npx wrangler secret put TURNSTILE_SECRET`.

The Worker rejects any submission whose token fails verification, whose `action` isn't
`contact`, or whose hostname isn't in `TURNSTILE_HOSTNAMES`.

### Security headers

`public/_headers` applies CSP, HSTS, nosniff, referrer and permissions policies to every
static response; `src/worker.js` applies the same set to its own responses. The CSP has no
`unsafe-inline` scripts. If you add an inline `<script>` or `style=""` attribute, it will
be blocked; put it in a file instead.

### Optional: cookieless analytics

If you want visitor counts, use **Cloudflare Web Analytics** (no cookies, no personal
data) from the dashboard. Prefer the "automatic setup" that injects nothing into your HTML,
or, if you add the beacon script, extend `script-src` and `connect-src` in both
`_headers` and `worker.js` to `https://static.cloudflareinsights.com` and
`https://cloudflareinsights.com`, then mention it in the privacy policy.

## Launch checklist

- [ ] Every `TODO:` below is resolved and `grep -r "TODO" src public` returns nothing
- [ ] Fonts added to `public/fonts/` (see `public/fonts/README.md`)
- [ ] Real headshot replaces `images/headshot-placeholder.svg`, with descriptive alt text
- [ ] Turnstile site key replaced in `contact.html`; secret set with `wrangler secret put`
- [ ] Email Service domain onboarded; `CONTACT_TO` / `CONTACT_FROM` set
- [ ] Custom domain attached
- [ ] Each page validated at https://validator.w3.org/ and scanned with axe DevTools
- [ ] Crisis notice visible in the footer of every page and beside the contact form
- [ ] Contact form rejects submissions without a valid Turnstile token (test with the
      "always fails" test secret `2x0000000000000000000000000000000AA`)
- [ ] Browser Network tab on page load shows only requests to your domain
      (Contact page additionally shows `challenges.cloudflare.com`)
- [ ] https://securityheaders.com reports A or better
- [ ] Site works with JavaScript disabled (nav is a plain list, FAQ fully expanded,
      form posts normally and lands on `/thank-you`)
- [ ] Lighthouse 95+ on mobile for Home and Contact
- [ ] Privacy Policy and Notice of Privacy Practices reviewed by legal/compliance

## Every `TODO:` that needs the owner

Practice details (appear on multiple pages and in the footer):

- Clinician name and credentials
- License type, number, and state(s)
- Location: office address, or "telehealth only, serving STATE"
- Session formats offered (telehealth / in person / both)
- Populations served (e.g. adults 18+)
- Phone number, public email, office hours, response-time expectation
- Client portal URL and platform name
- Telehealth platform name

Page-specific:

- **Home:** the three "who I work with" items; the intro paragraph; photo alt text
- **About:** bio paragraphs; degree; modalities; certifications; state board license-lookup
  link; optional "outside the office" line
- **Services:** confirm each specialty is actually treated; couples/family yes or no;
  modality list; session length
- **What to expect:** reply time; portal name; parking/entry notes; cancellation window
- **Fees:** rates; initial-session rate (or remove); sliding scale yes/no; payment method;
  in-network vs out-of-network wording; cancellation fee; compliance review of the Good
  Faith Estimate notice
- **FAQ:** platform name; state(s); session length; license type
- **Contact:** phone as `tel:` link; email; hours; response time; address and a real map
  link; portal URL; **Turnstile site key**
- **Privacy policy:** legal entity; contact; date; state disclosures; analytics if enabled
- **Notice of Privacy Practices:** replace the placeholder with the practice's approved
  notice
- **Crisis resources:** local crisis line, mobile crisis team, nearest ER; after-hours policy;
  date the numbers were verified
- **Structured data (index.html JSON-LD):** telephone, email, address, area served,
  hours, founder name and title
- **wrangler.jsonc:** `CONTACT_TO`
- **Footer:** phone, email, location, clinician name, license

## Assumptions made without the owner

- **US-based practice.** Crisis notice uses 988 and 911; the Good Faith Estimate notice
  assumes the No Surprises Act applies. Change both if outside the US.
- **Individual adult therapy** is the default framing. Couples, families, and adolescents
  are marked TODO rather than assumed.
- **Email delivery via Cloudflare Email Service** (first-party, no extra vendor, no API
  key to leak). It requires the Workers paid plan; the README shows how to swap in Resend.
- **Fonts:** Newsreader and Atkinson Hyperlegible Next were chosen but the font files are
  not in the repo (they need to be downloaded and subset by the owner or developer).
  Fallbacks are in place so nothing breaks.
- **Turnstile test key** is in `contact.html` so the form works locally out of the box.
  In production the real secret will reject it until replaced; the form fails closed.
- **Logo and palette** come from the Claude Design "summer green" direction (see `DESIGN.md`,
  revision 2). The illustrated mark is a raster PNG/WebP, so it is served at fixed sizes.
- **The map link points to OpenStreetMap** rather than Google to avoid sending referrer
  data to an ad network. Swap it if the owner prefers Google Maps.
- **Copy is written in first person** ("I work with…") on the assumption of a solo
  clinician. If there are several, change to "we" throughout `src/pages/`.
