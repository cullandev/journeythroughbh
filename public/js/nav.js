// Mobile navigation: toggle button, focus trap while open, Escape to close,
// focus restored to the button. On wide screens the CSS shows the nav and
// hides the button, so this only matters below 60em.
(function () {
  "use strict";
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (!toggle || !nav) return;

  var mq = window.matchMedia("(min-width: 60em)");
  var focusable = 'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])';

  function isOpen() { return toggle.getAttribute("aria-expanded") === "true"; }

  function open() {
    nav.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    var first = nav.querySelector(focusable);
    if (first) first.focus();
    document.addEventListener("keydown", onKey);
    document.addEventListener("click", onOutside, true);
  }

  function close(restore) {
    if (!mq.matches) nav.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
    document.removeEventListener("keydown", onKey);
    document.removeEventListener("click", onOutside, true);
    if (restore) toggle.focus();
  }

  function onKey(e) {
    if (e.key === "Escape") { close(true); return; }
    if (e.key !== "Tab") return;
    var items = Array.prototype.slice.call(nav.querySelectorAll(focusable));
    items.unshift(toggle);
    var first = items[0], last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  function onOutside(e) {
    if (!nav.contains(e.target) && !toggle.contains(e.target)) close(false);
  }

  function sync() {
    if (mq.matches) { nav.hidden = false; toggle.setAttribute("aria-expanded", "false"); }
    else if (!isOpen()) { nav.hidden = true; }
  }

  toggle.addEventListener("click", function () { isOpen() ? close(true) : open(); });
  if (mq.addEventListener) mq.addEventListener("change", sync); else mq.addListener(sync);
  sync();
})();
