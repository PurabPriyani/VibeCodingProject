// Dashboard: the cash flow bar chart and the status filter on recent invoices.

const chartBox = document.getElementById("bar-chart");

if (chartBox) {
  const months = JSON.parse(document.getElementById("monthly-data").textContent);
  const money = new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD", maximumFractionDigits: 0 });

  // The tallest bar fills the chart and every other bar is sized against it.
  let highest = 0;
  for (let i = 0; i < months.length; i++) {
    if (months[i].value > highest) {
      highest = months[i].value;
    }
  }

  for (let i = 0; i < months.length; i++) {
    let percent = 0;
    if (highest > 0) {
      percent = (months[i].value / highest) * 100;
    }

    const column = document.createElement("div");
    column.className = "bar-col";
    if (i === months.length - 1) {
      column.classList.add("is-current");
    }

    column.innerHTML =
      '<span class="bar-value">' + money.format(months[i].value) + "</span>" +
      '<div class="bar-track"><div class="bar"></div></div>' +
      '<span class="bar-label">' + months[i].label + "</span>";

    chartBox.appendChild(column);

    // Grow each bar a little after the one before it.
    const bar = column.querySelector(".bar");
    setTimeout(function () {
      bar.style.height = Math.max(percent, 2) + "%";
    }, 120 + i * 80);
  }
}

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
