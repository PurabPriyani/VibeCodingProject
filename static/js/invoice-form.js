// Invoice builder: add/remove line items and keep the totals live.
// The server recalculates everything on save, so these numbers are only
// a preview for the person filling in the form.

const form = document.getElementById("invoice-form");

if (form) {
  const itemsBox = document.getElementById("items");
  const template = document.getElementById("item-template");
  const totalForms = document.getElementById("id_items-TOTAL_FORMS");
  const taxRate = parseFloat(form.dataset.taxRate) || 0;

  const issueInput = document.getElementById("id_issue_date");
  const termsInput = document.getElementById("id_terms");

  const money = new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD" });

  // Round to cents the same way the server does, so the preview never
  // disagrees with the saved invoice.
  function toCents(value) {
    return Math.round(value * 100) / 100;
  }

  function visibleRows() {
    const rows = [];
    const all = itemsBox.querySelectorAll(".js-item-row");
    for (let i = 0; i < all.length; i++) {
      if (!all[i].classList.contains("is-removed")) {
        rows.push(all[i]);
      }
    }
    return rows;
  }

  function updateTotals() {
    let subtotal = 0;
    const rows = visibleRows();

    for (let i = 0; i < rows.length; i++) {
      const qty = parseFloat(rows[i].querySelector(".js-qty").value) || 0;
      const price = parseFloat(rows[i].querySelector(".js-price").value) || 0;
      const lineTotal = toCents(qty * price);

      rows[i].querySelector(".js-line-total").textContent = money.format(lineTotal);
      subtotal += lineTotal;
    }

    subtotal = toCents(subtotal);
    const tax = toCents(subtotal * taxRate / 100);

    document.getElementById("subtotal").textContent = money.format(subtotal);
    document.getElementById("tax").textContent = money.format(tax);
    document.getElementById("total").textContent = money.format(subtotal + tax);
  }

  function updateDueDate() {
    const label = document.getElementById("due-date");
    if (!issueInput.value) {
      label.textContent = "—";
      return;
    }

    // Build the date from its parts so the browser's time zone can't shift it a day.
    const parts = issueInput.value.split("-");
    const due = new Date(parts[0], parts[1] - 1, parts[2]);
    due.setDate(due.getDate() + parseInt(termsInput.value, 10));

    label.textContent = due.toLocaleDateString("en-CA", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function removeRow(row) {
    // Always keep at least one line on the invoice.
    if (visibleRows().length === 1) {
      row.querySelectorAll("input[type='text'], input[type='number']").forEach(function (input) {
        input.value = "";
      });
      updateTotals();
      return;
    }

    // Django removes the item on save when its DELETE box is ticked,
    // so the row is hidden and ticked rather than taken out of the page.
    row.querySelector("input[type='checkbox']").checked = true;
    row.classList.add("is-removed");
    updateTotals();
  }

  document.getElementById("add-item").addEventListener("click", function () {
    const index = parseInt(totalForms.value, 10);
    const html = template.innerHTML.replace(/__prefix__/g, index);

    itemsBox.insertAdjacentHTML("beforeend", html);
    totalForms.value = index + 1;

    const rows = itemsBox.querySelectorAll(".js-item-row");
    rows[rows.length - 1].querySelector("input[type='text']").focus();
    updateTotals();
  });

  // One listener on the whole list handles rows added later as well.
  itemsBox.addEventListener("input", updateTotals);
  itemsBox.addEventListener("click", function (event) {
    const button = event.target.closest(".js-remove-item");
    if (button) {
      removeRow(button.closest(".js-item-row"));
    }
  });

  issueInput.addEventListener("change", updateDueDate);
  termsInput.addEventListener("change", updateDueDate);

  updateTotals();
  updateDueDate();
}
