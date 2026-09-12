# Security review of journeythroughbh.org

Date: 2026-09-11. Scope: the deployed site at `https://journeythroughbh.org`, the Worker
in `src/worker.js`, the client JavaScript, the security headers, the Cloudflare
configuration visible from outside, and the repository history. Method: source review
plus black-box probes against the live site (no load testing, no attempts to bypass
Turnstile beyond a single bogus-token submission).

Overall: the site's attack surface is small and the important controls are in place.
There is one blocking functional finding (the contact form cannot currently succeed for
real visitors), two medium items, and a handful of low-priority hardening notes.

## Findings

### 1. Production still serves the Turnstile *test* site key — the contact form fails closed

**Severity:** High (functional, not exploitable). **Status:** open, needs the owner.

The live Contact page renders the widget with site key `1x00000000000000000000AA`, the
"always passes" test key. Test keys produce a dummy token. The Worker sends that token to
Cloudflare's siteverify with the production secret, which rejects it (confirmed: a bogus
token returned `403 turnstile`). Result: every real visitor's submission is refused with
"The security check didn't pass."

This is the safe failure mode, but it means no inquiries can arrive through the form.

**Fix:** create the production widget (Turnstile → Add widget, hostnames
`journeythroughbh.org` and `www.journeythroughbh.org`), put its site key in
`src/pages/contact.html`, run `python scripts/build.py`, commit, push. Then confirm the
secret in the Worker matches that widget. Test with a real submission.

### 2. Until the domain fix deployed today, the hostname allowlist rejected the real site

**Severity:** Medium (functional). **Status:** fixed in `e431b54`.

`TURNSTILE_HOSTNAMES` was `journeythroughbh.com,www.journeythroughbh.com`; the site is
`.org`. Even with a correct site key, the Worker would have refused every token as coming
from an unexpected hostname. The canonical URLs, sitemap, robots, and structured data had
the same problem. All now say `.org` and are live.

### 3. No rate limit on `POST /api/contact`

**Severity:** Medium. **Status:** open, one dashboard rule.

Turnstile stops naive bots, but tokens can be solved by paid services at scale, and each
accepted submission sends one email. The Worker is stateless so it cannot throttle. A WAF
rate-limiting rule closes this cheaply:

- Zone → Security → WAF → Rate limiting rules → Create.
- Expression: `(http.request.uri.path eq "/api/contact" and http.request.method eq "POST")`
- 10 requests per 1 minute per IP, block for 1 hour.

Also enable Bot Fight Mode (Security → Bots) on the free plan.

### 4. `www.journeythroughbh.org` does not respond

**Severity:** Low (availability/SEO, not security). **Status:** open.

HTTPS to the `www` hostname gets no response, so it is not attached as a custom domain and
there is no certificate for it. Anyone typing `www.` gets a browser error. Attach it as a
second custom domain on the Worker, then add the "Redirect from WWW to root" rule so it
301s to the apex.

### 5. Email subject built from user input without newline stripping

**Severity:** Low. **Status:** open, one-line fix recommended.

`subject: \`Website inquiry from ${name}\``. The name is length-capped and trimmed but a
`\r\n` inside it is not removed. Cloudflare's Email Service takes a JSON object and
should encode or reject this, so header injection is unlikely, but the Worker shouldn't
rely on that. Strip control characters from `name` before use:

```js
const name = str("name").replace(/[\r\n\t]+/g, " ").slice(0, LIMITS.name);
```

### 6. HSTS with `includeSubDomains; preload`

**Severity:** Informational. **Status:** by design; be aware.

Both `_headers` and the Worker send `max-age=63072000; includeSubDomains; preload`.
This is correct for a site with no HTTP-only subdomains. Two consequences to know:
once browsers cache it, every future subdomain must be HTTPS (Email Service's
`cf-bounce.` subdomain is MX/TXT only, so unaffected); and if you submit to the
preload list, removal takes months. Do not add subdomains that can't serve HTTPS.

### 7. Cloudflare's managed robots.txt is prepended to yours

**Severity:** Informational.

The live `robots.txt` starts with a Cloudflare-managed block that disallows a list of AI
crawlers and adds Content-Signal directives, then your own rules. That means the zone has
"Manage AI bots / managed robots.txt" enabled. Harmless, and arguably good for a
therapy site, but it is a zone setting you didn't put in the repo; know it's there.

### 8. Placeholder outbound links are live

**Severity:** Low (professionalism, and a phishing-style risk if someone ever registers
the placeholder domain). **Status:** open, part of the TODO list.

The Contact page links "Client portal" to `https://TODO.example.com` and the map to an
OpenStreetMap search for "TODO". `example.com` is reserved by IANA so it can't be
hijacked, but the links should be replaced or removed before the site is publicised.

## What was checked and found sound

**Headers (live, every page and the API route).** CSP with no `unsafe-inline`, no
`unsafe-eval`, `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`,
`frame-ancestors 'none'`; HSTS; `X-Content-Type-Options: nosniff`;
`Referrer-Policy: strict-origin-when-cross-origin`; restrictive `Permissions-Policy`;
`X-Frame-Options: DENY`; `Cache-Control: no-store` on the API route. The 404 page and
Worker-generated responses carry the same set. This scores A+ territory on
securityheaders.com.

**Only two external origins.** Page loads touch `journeythroughbh.org` and, on Contact
only, `challenges.cloudflare.com`. The map link to OpenStreetMap is a plain anchor. No
fonts, analytics, pixels, or embeds. No cookies are set, so no consent banner is owed.

**Transport.** TLS 1.0 refused; TLS 1.2 accepted; HTTP 301s to HTTPS; certificate valid.

**Source and config exposure.** `wrangler.jsonc`, `.dev.vars*`, `_headers`,
`package.json`, `src/`, `scripts/`, `.git/`, `.claude/`, and `README.md` all return 404.
Only `public/` is served.

**API route.** GET, PUT, DELETE, OPTIONS all return 405. Cross-origin POST with a
foreign `Origin` header is refused. Missing or bogus Turnstile tokens are refused (fails
closed). Field lengths are enforced server-side. The honeypot silently discards bots.
Error pages escape reflected text. No request body content is ever logged.

**Secrets.** No secrets in the repo or its history (scanned all commits). The Turnstile
secret lives only as a Worker secret. `.dev.vars` is gitignored.

**Client JavaScript.** No `eval`, no `innerHTML` with user data (the one `innerHTML` call
writes a static string), no third-party scripts except Turnstile, no `localStorage`.
Everything degrades to plain HTML with JavaScript off.

**PHI handling.** The form collects name, contact method, email/phone, and a short
optional message; it tells the visitor not to include health details; nothing is stored
by the site; delivery is by email to the practice with a reminder not to forward.
Intake lives in the client portal. This matches the brief. Note that the delivery email
itself is only as private as the receiving inbox; use a HIPAA-appropriate mailbox for
`CONTACT_TO`.

**Dependencies.** None at runtime. `wrangler` is a dev dependency used only by Workers
Builds.

## Priority order

1. Replace the Turnstile test site key (finding 1). Nothing else matters until the form
   works.
2. Add the WAF rate-limit rule and Bot Fight Mode (finding 3).
3. Attach `www` and redirect it (finding 4).
4. Strip newlines from `name` in the Worker (finding 5).
5. Replace the placeholder links along with the rest of the TODO list (finding 8).
