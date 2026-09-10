// Contact form enhancement. The form works as a normal POST without this
// file; with it, we validate inline, submit with fetch, and show the result
// in place without a page reload.
(function () {
  "use strict";
  var form = document.getElementById("contact-form");
  if (!form || !window.fetch) return;

  var status = document.getElementById("form-status");
  var submit = form.querySelector('button[type="submit"]');
  var message = form.querySelector("#message");
  var count = document.getElementById("message-count");
  var MAX = 500;

  function setError(name, text) {
    var field = form.querySelector('[data-field="' + name + '"]');
    var msg = field && field.querySelector(".error-msg");
    if (!field || !msg) return;
    msg.textContent = text || "";
    if (text) field.setAttribute("data-invalid", ""); else field.removeAttribute("data-invalid");
    var input = field.querySelector("input, textarea");
    if (input) input.setAttribute("aria-invalid", text ? "true" : "false");
  }

  function showStatus(kind, text) {
    status.className = "form-status notice " + (kind === "error" ? "is-error" : "is-success");
    status.textContent = text;
  }

  function validate() {
    var ok = true;
    var name = form.name.value.trim();
    var method = form.querySelector('input[name="method"]:checked');
    var email = form.email.value.trim();
    var phone = form.phone.value.trim();

    setError("name", ""); setError("method", ""); setError("email", ""); setError("phone", ""); setError("message", "");

    if (!name) { setError("name", "Please tell us what to call you."); ok = false; }
    if (!method) { setError("method", "Choose how you'd like us to reply."); ok = false; }
    if (method && method.value === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("email", "Enter an email address we can reply to."); ok = false;
    }
    if (method && method.value === "phone" && phone.replace(/\D/g, "").length < 10) {
      setError("phone", "Enter a phone number with area code."); ok = false;
    }
    if (message.value.length > MAX) { setError("message", "Please keep your message under " + MAX + " characters."); ok = false; }
    return ok;
  }

  if (message && count) {
    var updateCount = function () { count.textContent = (MAX - message.value.length) + " characters left"; };
    message.addEventListener("input", updateCount);
    updateCount();
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    status.textContent = "";
    if (!validate()) {
      var firstBad = form.querySelector('[data-invalid] input, [data-invalid] textarea');
      if (firstBad) firstBad.focus();
      return;
    }

    var turnstile = form.querySelector('[name="cf-turnstile-response"]');
    if (turnstile && !turnstile.value) {
      showStatus("error", "The security check hasn't finished yet. Give it a second and try again.");
      return;
    }

    submit.disabled = true;
    submit.textContent = "Sending…";

    fetch(form.action, {
      method: "POST",
      headers: { "Accept": "application/json" },
      body: new FormData(form)
    }).then(function (r) {
      return r.json().then(function (data) { return { ok: r.ok, data: data }; });
    }).then(function (res) {
      if (res.ok && res.data && res.data.ok) {
        var done = document.createElement("div");
        done.className = "notice is-success";
        done.setAttribute("tabindex", "-1");
        done.innerHTML = "<p><strong>Thanks, your message is on its way.</strong></p>" +
          "<p>We'll reply by the method you chose, usually within " +
          "<mark class=\"todo\">TODO: response time</mark>. " +
          "If you don't hear back, check your spam folder or call " +
          "<mark class=\"todo\">TODO: phone</mark>.</p>";
        form.replaceWith(done);
        done.focus();
        return;
      }
      var msg = (res.data && res.data.message) || "Something went wrong on our end. You can also email or call us directly.";
      showStatus("error", msg);
      if (res.data && res.data.field) setError(res.data.field, msg);
      if (window.turnstile && typeof window.turnstile.reset === "function") window.turnstile.reset();
    }).catch(function () {
      showStatus("error", "We couldn't reach the server. Check your connection and try again, or email or call us directly.");
      if (window.turnstile && typeof window.turnstile.reset === "function") window.turnstile.reset();
    }).finally(function () {
      submit.disabled = false;
      submit.textContent = "Send message";
    });
  });
})();
