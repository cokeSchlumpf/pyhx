// Copy-to-clipboard for the pyhx code component. Event-delegated so it works
// for any number of code blocks, including fragment-swapped content. Only the
// active part's panel is ever in the DOM, so the handler reads it directly.
(function () {
  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".hx-code__copy");
    if (!btn) return;
    var shell = btn.closest(".hx-code__shell");
    var panel = shell && shell.querySelector(".hx-code__panel");
    if (!panel || !navigator.clipboard) return;
    navigator.clipboard.writeText(panel.innerText).then(function () {
      btn.classList.add("is-copied");
      setTimeout(function () { btn.classList.remove("is-copied"); }, 1200);
    });
  });
})();
