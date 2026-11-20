// Small things every page needs.

// Toast messages slide away on their own after a few seconds.
document.querySelectorAll(".toast").forEach(function (toast) {
  setTimeout(function () {
    toast.classList.add("is-leaving");
    setTimeout(function () {
      toast.remove();
    }, 300);
  }, 3500);
});

// Any form with the js-confirm class asks before it submits (used for deletes).
document.querySelectorAll("form.js-confirm").forEach(function (form) {
  form.addEventListener("submit", function (event) {
    if (!window.confirm(form.dataset.confirm)) {
      event.preventDefault();
    }
  });
});

// Print button. Save as PDF is in the browser's print dialog, so there's
// no PDF library to install.
document.querySelectorAll(".js-print").forEach(function (button) {
  button.addEventListener("click", function () {
    window.print();
  });
});
