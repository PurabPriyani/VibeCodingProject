// Dashboard: the status filter on recent invoices.

const chips = document.querySelectorAll("#status-chips .chip");
const recentRows = document.querySelectorAll(".js-recent-row");
const noRecent = document.getElementById("no-recent");

chips.forEach(function (chip) {
  chip.addEventListener("click", function () {
    chips.forEach(function (other) {
      other.classList.remove("is-active");
    });
    chip.classList.add("is-active");

    const filter = chip.dataset.filter;
    let visible = 0;

    recentRows.forEach(function (row) {
      if (filter === "all" || row.dataset.status === filter) {
        row.hidden = false;
        visible++;
      } else {
        row.hidden = true;
      }
    });

    noRecent.classList.toggle("is-hidden", visible > 0);
  });
});
