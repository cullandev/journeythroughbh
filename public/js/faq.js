// FAQ accordion, progressively enhanced. Without JS every answer is simply
// visible. With JS each heading becomes a real <button> with aria-expanded
// controlling its panel; arrow keys move between questions.
(function () {
  "use strict";
  var items = document.querySelectorAll(".faq-item");
  if (!items.length) return;

  var buttons = [];
  Array.prototype.forEach.call(items, function (item, i) {
    var heading = item.querySelector("h3");
    var panel = item.querySelector(".faq-panel");
    if (!heading || !panel) return;

    var btn = document.createElement("button");
    btn.type = "button";
    btn.id = "faq-q-" + i;
    panel.id = panel.id || "faq-a-" + i;
    btn.setAttribute("aria-controls", panel.id);
    btn.setAttribute("aria-expanded", "false");
    while (heading.firstChild) btn.appendChild(heading.firstChild);
    heading.appendChild(btn);
    panel.setAttribute("aria-labelledby", btn.id);
    panel.hidden = true;

    btn.addEventListener("click", function () {
      var expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!expanded));
      panel.hidden = expanded;
    });
    buttons.push(btn);
  });

  buttons.forEach(function (btn, i) {
    btn.addEventListener("keydown", function (e) {
      var next = null;
      if (e.key === "ArrowDown") next = buttons[(i + 1) % buttons.length];
      else if (e.key === "ArrowUp") next = buttons[(i - 1 + buttons.length) % buttons.length];
      else if (e.key === "Home") next = buttons[0];
      else if (e.key === "End") next = buttons[buttons.length - 1];
      if (next) { e.preventDefault(); next.focus(); }
    });
  });

  // Open a question directly linked by hash, e.g. /faq#confidentiality
  if (location.hash) {
    var target = document.getElementById(location.hash.slice(1));
    var item = target && target.closest(".faq-item");
    if (item) {
      var b = item.querySelector("button");
      if (b) b.click();
    }
  }
})();
