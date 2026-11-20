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

// Any form with the js-confirm class asks before it submits (deletes, sending emails).
document.querySelectorAll("form.js-confirm").forEach(function (form) {
  form.addEventListener("submit", function (event) {
    if (!window.confirm(form.dataset.confirm)) {
      event.preventDefault();
      return;
    }

    // Sending an email can take a few seconds, so show that something is
    // happening and stop the button being clicked twice.
    const button = form.querySelector(".js-sending");
    if (button) {
      button.disabled = true;
      button.innerHTML = '<i class="ti ti-loader-2 spin"></i> Sending...';
    }
  });
});

// Print button. The print stylesheet hides everything except the invoice,
// and the browser's print dialog can also save it as a PDF.
document.querySelectorAll(".js-print").forEach(function (button) {
  button.addEventListener("click", function () {
    window.print();
  });
});
