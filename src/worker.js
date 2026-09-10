/**
 * Journey Through Behavioral Health — Worker
 *
 * Static assets are served directly by Workers Static Assets (this script is
 * only invoked when no asset matches). The single dynamic route is
 * POST /api/contact, which:
 *   1. reads a standard form post (works with JS disabled),
 *   2. validates + length-limits every field,
 *   3. verifies the Cloudflare Turnstile token server-side,
 *   4. sends the message by email through the Cloudflare Email Service binding,
 *   5. answers with JSON (fetch) or a redirect / small HTML page (plain form).
 *
 * Nothing from the message body is ever logged.
 */

const LIMITS = { name: 100, email: 254, phone: 40, message: 500 };
const SITEVERIFY = "https://challenges.cloudflare.com/turnstile/v0/siteverify";

const SECURITY_HEADERS = {
  "Content-Security-Policy":
    "default-src 'self'; script-src 'self' https://challenges.cloudflare.com; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-src https://challenges.cloudflare.com; form-action 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; upgrade-insecure-requests",
  "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=(), browsing-topics=()",
  "X-Frame-Options": "DENY",
  "Cache-Control": "no-store",
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/contact") {
      if (request.method !== "POST") {
        return withHeaders(new Response("Method not allowed", { status: 405, headers: { Allow: "POST" } }));
      }
      return handleContact(request, env);
    }

    // Anything else: let static assets answer (this yields 404.html for unknown paths).
    return env.ASSETS.fetch(request);
  },
};

async function handleContact(request, env) {
  const wantsJson = (request.headers.get("Accept") || "").includes("application/json");
  const reply = (status, body) => respond(wantsJson, status, body);

  // Same-origin check: the form must be posted from this site.
  const origin = request.headers.get("Origin");
  if (origin && origin !== new URL(request.url).origin) {
    return reply(403, { ok: false, error: "origin", message: "This form can only be sent from our website." });
  }

  let form;
  try {
    form = await request.formData();
  } catch {
    return reply(400, { ok: false, error: "body", message: "We couldn't read the form. Please try again." });
  }

  const str = (k) => {
    const v = form.get(k);
    return typeof v === "string" ? v.trim() : "";
  };

  // Honeypot: real people never see or fill this field.
  if (str("website")) {
    return reply(200, { ok: true }); // pretend success, discard silently
  }

  const name = str("name").slice(0, LIMITS.name);
  const method = str("method");
  const email = str("email").slice(0, LIMITS.email);
  const phone = str("phone").slice(0, LIMITS.phone);
  const message = str("message");

  if (!name) return reply(400, { ok: false, error: "validation", field: "name", message: "Please tell us what to call you." });
  if (method !== "email" && method !== "phone") {
    return reply(400, { ok: false, error: "validation", field: "method", message: "Choose how you'd like us to reply." });
  }
  if (method === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return reply(400, { ok: false, error: "validation", field: "email", message: "Enter an email address we can reply to." });
  }
  if (method === "phone" && phone.replace(/\D/g, "").length < 10) {
    return reply(400, { ok: false, error: "validation", field: "phone", message: "Enter a phone number with area code." });
  }
  if (message.length > LIMITS.message) {
    return reply(400, { ok: false, error: "validation", field: "message", message: `Please keep your message under ${LIMITS.message} characters.` });
  }

  // Turnstile: verify the token server-side. Fails closed.
  const token = str("cf-turnstile-response");
  const verified = await verifyTurnstile(token, request, env);
  if (!verified) {
    return reply(403, { ok: false, error: "turnstile", message: "The security check didn't pass. Please try again." });
  }

  // Deliver. Only plain text; the visitor's content is escaped by not being HTML at all.
  const to = env.CONTACT_TO;
  const from = env.CONTACT_FROM;
  if (!to || !from || !env.EMAIL) {
    console.error("Contact form not configured: missing CONTACT_TO, CONTACT_FROM, or EMAIL binding");
    return reply(500, { ok: false, error: "config", message: "The form isn't set up yet. Please email or call us directly." });
  }

  const lines = [
    "New message from the website contact form",
    "",
    `Name: ${name}`,
    `Preferred contact: ${method}`,
    method === "email" ? `Email: ${email}` : `Phone: ${phone}`,
    "",
    "Message:",
    message || "(none)",
    "",
    "Reminder: reply through a HIPAA-appropriate channel. Do not forward this email.",
  ];

  try {
    await env.EMAIL.send({
      from: { email: from, name: "Website contact form" },
      to,
      replyTo: method === "email" ? email : undefined,
      subject: `Website inquiry from ${name}`,
      text: lines.join("\n"),
    });
  } catch (err) {
    // Log the failure class only, never the content.
    console.error("Email send failed:", err && err.name ? err.name : "unknown");
    return reply(502, { ok: false, error: "delivery", message: "We couldn't send your message right now. Please email or call us directly." });
  }

  return reply(200, { ok: true });
}

async function verifyTurnstile(token, request, env) {
  if (!token || token.length > 2048 || !env.TURNSTILE_SECRET) return false;
  const expectedHosts = new Set(
    (env.TURNSTILE_HOSTNAMES || "").split(",").map((h) => h.trim()).filter(Boolean),
  );
  try {
    const r = await fetch(SITEVERIFY, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      signal: AbortSignal.timeout(10_000),
      body: new URLSearchParams({
        secret: env.TURNSTILE_SECRET,
        response: token,
        remoteip: request.headers.get("CF-Connecting-IP") || "",
      }),
    });
    if (!r.ok) return false;
    const result = await r.json();
    if (!result.success) return false;
    if (result.action && result.action !== "contact") return false;
    // Hostname check is enforced only when a list is configured (empty during local dev).
    if (expectedHosts.size > 0 && !expectedHosts.has(result.hostname)) return false;
    return true;
  } catch {
    return false;
  }
}

function respond(wantsJson, status, body) {
  if (wantsJson) {
    return withHeaders(Response.json(body, { status }));
  }
  if (body.ok) {
    return withHeaders(new Response(null, { status: 303, headers: { Location: "/thank-you" } }));
  }
  // Plain-HTML fallback for visitors without JavaScript.
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Message not sent · Journey Through Behavioral Health</title>
<link rel="stylesheet" href="/css/site.css"></head>
<body><main class="wrap section"><h1>We couldn't send that</h1>
<p class="lead">${escapeHtml(body.message || "Something went wrong.")}</p>
<p><a href="/contact#contact-form">Go back to the form</a> and try again, or email or call us directly.</p>
<p><small>If you are in crisis, call or text 988 (Suicide &amp; Crisis Lifeline) or call 911.</small></p>
</main></body></html>`;
  return withHeaders(new Response(html, { status, headers: { "Content-Type": "text/html; charset=utf-8" } }));
}

function withHeaders(res) {
  const out = new Response(res.body, res);
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) out.headers.set(k, v);
  return out;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
