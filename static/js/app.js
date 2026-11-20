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
