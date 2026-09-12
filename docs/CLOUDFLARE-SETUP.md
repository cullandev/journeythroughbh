# Cloudflare setup, end to end

Everything needed to take this repo from GitHub to a live site at `journeythroughbh.org`,
in the order that avoids backtracking. Verified against Cloudflare's documentation on
2026-09-11. Dashboard labels drift, so if a menu item is named slightly differently,
look for the nearest match.

**Plan requirement in one line:** the Workers **Free** plan is enough, provided the
contact form's `CONTACT_TO` inbox is added as a *verified destination address* in
Email Routing (sending to verified addresses is free on all plans). Sending to any
other address needs Workers Paid ($5/month).

---

## 0. Before you start

You need:

- A Cloudflare account (free) at https://dash.cloudflare.com.
- The GitHub repo pushed, with `main` as the branch you want live.
- Access to wherever `journeythroughbh.org` is registered (to change nameservers), or
  the domain not yet purchased (Cloudflare Registrar sells domains at cost).
- Node.js on any machine where you want to run `wrangler` commands. Every step below
  can also be done in the dashboard, so Node is optional.

Order matters:

1. Domain onto Cloudflare DNS (everything else hangs off the zone).
2. Worker created from the GitHub repo (Workers Builds).
3. Custom domain attached to the Worker.
4. Turnstile widget, then its secret into the Worker.
5. Email Service, then `CONTACT_TO` / `CONTACT_FROM` set.
6. Redirect `www` to the apex.
7. Hardening and verification.

---

## 1. Put the domain on Cloudflare DNS

Email Service, Custom Domains, redirect rules, and Turnstile hostname checks all require
the zone to be on Cloudflare DNS.

**If the domain is registered elsewhere**

1. Dashboard → **Add a domain** → type `journeythroughbh.org` → **Quick scan for DNS
   records** → choose the **Free** plan.
2. Cloudflare shows two nameservers (`*.ns.cloudflare.com`). At your registrar, replace
   the existing nameservers with those two.
3. Wait for the zone to show **Active** (minutes to a day). Cloudflare emails you.
4. Delete any stray `A`/`CNAME` records for `@` and `www` that the scan imported from a
   previous host. The Worker custom domain will create its own, and it refuses to
   attach to a hostname that already has a CNAME.

**If buying new**

Dashboard → **Domain Registration** → **Register Domains** → buy it. It lands on
Cloudflare DNS automatically, already Active.

**Zone settings worth setting now** (Dashboard → the domain → **SSL/TLS**):

- **Overview → Encryption mode:** Full (strict). Workers custom domains are always
  HTTPS, so there's no origin to worry about.
- **Edge Certificates → Always Use HTTPS:** On.
- **Edge Certificates → HTTP Strict Transport Security (HSTS):** Enable, max-age 12
  months, include subdomains, preload. The site's `_headers` already sends HSTS, so
  this is belt-and-braces; enabling it here also covers redirects served by Cloudflare
  before the Worker.
- **Edge Certificates → Minimum TLS Version:** 1.2.

---

## 2. Create the Worker from the GitHub repo (Workers Builds)

1. Dashboard → **Compute & AI → Workers & Pages → Create → Import a repository**
   (labelled "Connect to Git" in some accounts).
2. Authorize the Cloudflare GitHub app for the `journeythroughbh` repository only.
3. Pick the repo. Cloudflare reads `wrangler.jsonc` and pre-fills the project name
   `journeythroughbh`.
4. Build settings:

   | Setting | Value |
   |---|---|
   | Production branch | `main` |
   | Build command | *(leave empty)* — the HTML is committed; nothing to compile |
   | Deploy command | `npx wrangler deploy` (the default) |
   | Non-production branch deploy command | `npx wrangler versions upload` (the default) |
   | Root directory | `/` |
   | Build variables | none needed |

5. **Save and Deploy**. The first build runs in about a minute and gives you a
   `https://journeythroughbh.<your-subdomain>.workers.dev` URL. Open it: the site should
   render with fallback fonts and all the amber TODO marks.

6. **Settings → Build → Branch control**: turn on **Non-production branch builds** so
   every pull request gets a preview URL and a PR comment with the link.
   `preview_urls` is already enabled in `wrangler.jsonc`.

7. **Settings → Domains & Routes → workers.dev**: leave it enabled for now. It's
   handy for testing. Once the custom domain is live you can disable it so the site
   has one canonical hostname. (`_headers` already tells search engines not to index
   `*.workers.dev`.)

What Workers Builds does on every push to `main`: checks out the commit, runs
`npx wrangler deploy` using the wrangler version pinned in `package.json`, uploads
`public/` as static assets and `src/worker.js` as the Worker, and promotes it to
production. Pushes to other branches upload a preview version without promoting it.

**Deploy failures to expect and fix**

- *"Binding EMAIL: Email Sending is not enabled"* or similar — Email Service isn't set
  up yet (step 5). Either finish step 5 first, or temporarily comment out the
  `send_email` block in `wrangler.jsonc`, deploy, and restore it after step 5.
- *Wrangler version prompt* — Workers Builds uses the `wrangler` in `package.json`
  devDependencies (`^4`). Keep it there.

---

## 3. Attach the custom domain

1. Worker → **Settings → Domains & Routes → Add → Custom Domain**.
2. Enter `journeythroughbh.org` → **Add Custom Domain**.
3. Repeat for `www.journeythroughbh.org`.

Cloudflare creates the DNS records and issues certificates automatically. Both
hostnames now serve the Worker. Give it a couple of minutes, then open
`https://journeythroughbh.org`.

If you prefer configuration as code, the equivalent in `wrangler.jsonc` is:

```jsonc
"routes": [
  { "pattern": "journeythroughbh.org", "custom_domain": true },
  { "pattern": "www.journeythroughbh.org", "custom_domain": true }
]
```

Either works; the dashboard route is simpler for a one-off.

---

## 4. Turnstile (spam protection on the contact form)

Turnstile is account-level, not zone-level.

1. Dashboard → **Turnstile → Add widget**.
2. Settings:

   | Setting | Value |
   |---|---|
   | Widget name | Journey Through BH contact form |
   | Hostname management | `journeythroughbh.org`, `www.journeythroughbh.org`, and your `*.workers.dev` hostname if you want the form to work on previews |
   | Widget mode | **Managed** (shows a checkbox only when it's unsure; invisible for most people) |
   | Pre-clearance | Off |

3. **Create** → copy the **Site key** and **Secret key**.
4. Site key into the page: in `src/pages/contact.html`, replace `1x00000000000000000000AA`
   with the real site key, run `python scripts/build.py`, commit, push. Workers Builds
   redeploys.
5. Secret key into the Worker as a secret (never in `wrangler.jsonc`):

   - Dashboard: Worker → **Settings → Variables & Secrets → Add** → Type **Secret**,
     name `TURNSTILE_SECRET`, paste the value → **Deploy**.
   - Or from a machine with Node: `npx wrangler secret put TURNSTILE_SECRET`.

6. Confirm `TURNSTILE_HOSTNAMES` (a plain variable, already in `wrangler.jsonc`)
   lists exactly the hostnames the form is served from. The Worker rejects tokens
   issued for any other hostname. Add the `workers.dev` hostname there too if you
   included it in the widget.

**Test that it fails closed.** Temporarily set `TURNSTILE_SECRET` to the "always
fails" test value `2x0000000000000000000000000000000AA`, submit the form, and confirm
the site shows "The security check didn't pass." Then put the real secret back.

---

## 5. Email delivery for the contact form (Cloudflare Email Service)

The Worker sends each inquiry through the `EMAIL` binding to `CONTACT_TO`, from
`CONTACT_FROM`.

### 5a. Onboard the sending domain

1. Dashboard → **Compute & AI → Email Service → Email Sending → Onboard Domain**.
2. Choose `journeythroughbh.org`. Cloudflare adds MX records on
   `cf-bounce.journeythroughbh.org`, plus SPF, DKIM, and DMARC TXT records, and locks
   them. Nothing to copy by hand because the zone is on Cloudflare DNS.
3. Wait for **Verified** (usually 5 to 15 minutes).

### 5b. Decide where inquiries go, and whether you need the paid plan

- **Free plan path:** go to **Email Service → Email Routing → Destination addresses →
  Add**, enter the practice inbox (for example the clinician's Gmail or Microsoft 365
  address), and click the verification link Cloudflare emails to it. Sending to a
  verified destination address is free on every plan and doesn't count against quota.
  Set `CONTACT_TO` to exactly that address.
- **Paid plan path:** if `CONTACT_TO` must be an address you can't verify (a shared
  helpdesk you don't control, for example), upgrade to Workers Paid under
  **Workers & Pages → Plans**. 3,000 outbound emails per month are included.

### 5c. Set the variables

Worker → **Settings → Variables & Secrets** (or edit `vars` in `wrangler.jsonc`, then
push):

| Variable | Value |
|---|---|
| `CONTACT_TO` | the verified practice inbox from 5b |
| `CONTACT_FROM` | `no-reply@journeythroughbh.org` (any address on the onboarded domain) |

`CONTACT_TO` lives only in the dashboard (so the inbox address isn't in the public repo);
`keep_vars: true` in `wrangler.jsonc` makes deploys preserve it. Any variable that *is*
in `wrangler.jsonc` is reset to the file's value on every deploy, so change those in
the file, not the dashboard.

### 5d. Optional: an inbox on the domain

If the practice wants `hello@journeythroughbh.org` to actually receive mail, use
**Email Routing → Routing rules → Create address** to forward it to the verified
destination address. Free, and unrelated to the contact form.

### 5e. Test

Submit the form on the live site. Within a minute the inbox should get
"Website inquiry from …" with a `Reply-To` of the visitor's email. If nothing
arrives, check **Email Service → Email Sending → Logs**, then
**Worker → Observability → Logs** for `Email send failed`.

---

## 6. Redirect `www` to the apex

Both hostnames serve the site after step 3, but search engines want one. The site's
canonical tags already point at the apex.

Dashboard → the domain → **Rules → Redirect Rules → Create rule** → template
**"Redirect from WWW to root"**, or manually:

| Field | Value |
|---|---|
| When incoming requests match | Hostname equals `www.journeythroughbh.org` |
| Then | Dynamic redirect, expression `concat("https://journeythroughbh.org", http.request.uri.path)`, status 301, preserve query string on |

Deploy. `https://www.journeythroughbh.org/about` should now land on
`https://journeythroughbh.org/about`.

---

## 7. Hardening (all optional, all free)

**Rate limit the form endpoint.** The Worker has no state, so Cloudflare's WAF is the
place. Domain → **Security → WAF → Rate limiting rules → Create rule**:
`(http.request.uri.path eq "/api/contact" and http.request.method eq "POST")`,
characteristic IP. On the Free plan the only allowed values are 5 requests per
10 seconds, action Block, duration 10 seconds; use those. On Pro and above prefer
10 requests per 1 minute, Managed Challenge, for 1 hour. Either is well above any real
human's rate and stops scripted floods that bypass the browser.

**Protect previews.** If pull-request preview URLs shouldn't be public,
Worker → **Settings → Domains & Routes → Preview URLs → Enable Cloudflare Access**,
then add an Access policy allowing only your email addresses.

**Bot Fight Mode.** Domain → **Security → Bots → Bot Fight Mode: On**. Free tier;
challenges known-bad bots before they reach the Worker.

**Disable workers.dev** once the custom domain is confirmed working, so there's a
single public hostname.

**Analytics without cookies (optional).** Domain → **Analytics & Logs → Web
Analytics → Enable**. Choose the automatic setup so no script is injected into your
HTML. If you instead add the beacon snippet, you must extend `script-src` and
`connect-src` in both `public/_headers` and `src/worker.js` and update the privacy
policy. Prefer automatic.

---

## 8. Verify the launch

Run through these on the live domain:

- [ ] `https://journeythroughbh.org` loads; `http://` redirects to `https://`; `www`
      redirects to the apex.
- [ ] https://securityheaders.com/?q=journeythroughbh.org scores **A** or better.
      (The CSP, HSTS, nosniff, referrer, permissions, and frame-ancestors headers
      come from `public/_headers`.)
- [ ] Browser Network tab on the home page shows only requests to
      `journeythroughbh.org`. On the Contact page, additionally
      `challenges.cloudflare.com`. Nothing else.
- [ ] No cookies are set (DevTools → Application → Cookies). So no cookie banner.
- [ ] The contact form: (a) sends and the email arrives; (b) fails with the
      always-fails Turnstile secret; (c) works with JavaScript disabled and lands on
      `/thank-you`.
- [ ] `https://journeythroughbh.org/does-not-exist` shows the branded 404 with a 404
      status.
- [ ] Lighthouse (Chrome DevTools) on mobile: 95+ on Home and Contact. Fonts must be
      in `public/fonts/` first or the font 404s will cost a few points.
- [ ] Google Search Console: add the property, submit
      `https://journeythroughbh.org/sitemap.xml`.
- [ ] Crisis notice visible in the footer of every page.

---

## 9. Day-to-day after launch

- **Edit copy:** change `src/pages/*.html`, run `python scripts/build.py`, commit,
  push to `main`. Live in about a minute. Or open a PR first and check the preview
  URL that Cloudflare comments on the PR.
- **Roll back:** Worker → **Deployments** → pick the previous version → **Rollback**.
- **Rotate the Turnstile secret:** Turnstile → widget → **Rotate secret key**, then
  update the `TURNSTILE_SECRET` secret on the Worker.
- **Logs:** Worker → **Observability → Logs**. The Worker never logs form contents,
  only error classes, so there's no PHI in the logs.
- **Costs:** Workers Free covers 100,000 requests per day, far above a therapy site's
  traffic. The only likely paid item is Email Sending if the destination inbox can't
  be verified (step 5b).

---

## Reference: what lives where

| Thing | Where it's configured |
|---|---|
| Site files | `public/` in the repo (deployed by Workers Builds) |
| Contact form handler | `src/worker.js` |
| Static-asset routing, bindings, plain variables | `wrangler.jsonc` |
| Security headers for pages | `public/_headers` |
| Security headers for `/api/contact` | `SECURITY_HEADERS` in `src/worker.js` |
| `TURNSTILE_SECRET` | Worker → Settings → Variables & Secrets (Secret) |
| Turnstile site key | `src/pages/contact.html` |
| `CONTACT_TO`, `CONTACT_FROM`, `TURNSTILE_HOSTNAMES` | `vars` in `wrangler.jsonc` |
| Sending domain, destination addresses | Compute & AI → Email Service |
| Custom domains | Worker → Settings → Domains & Routes |
| www redirect, HSTS, TLS | The zone → Rules / SSL/TLS |
| Rate limiting | The zone → Security → WAF |
| Build settings, branch control | Worker → Settings → Build |
