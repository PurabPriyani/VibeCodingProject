// Clients page: live search and the add / edit modal.

const modal = document.getElementById("client-modal");
const modalTitle = document.getElementById("client-modal-title");
const idInput = document.getElementById("client-id");
const searchInput = document.getElementById("client-search");

const fieldNames = ["name", "company", "email", "phone", "address"];

function clearErrors() {
  modal.querySelectorAll(".has-error").forEach(function (field) {
    field.classList.remove("has-error");
  });
  modal.querySelectorAll(".errorlist").forEach(function (list) {
    list.remove();
  });
}

function openModal(client) {
  clearErrors();

  if (client) {
    modalTitle.textContent = "Edit client";
    idInput.value = client.id;
  } else {
    modalTitle.textContent = "New client";
    idInput.value = "";
  }

  for (let i = 0; i < fieldNames.length; i++) {
    const name = fieldNames[i];
    const input = modal.querySelector("[name='" + name + "']");
    if (client) {
      input.value = client[name];
    } else {
      input.value = "";
    }
  }

  modal.showModal();
  modal.querySelector("[name='name']").focus();
}

document.getElementById("add-client").addEventListener("click", function () {
  openModal(null);
});

document.querySelectorAll(".js-edit-client").forEach(function (button) {
  button.addEventListener("click", function () {
    // dataset already holds id, name, company, email, phone and address
    openModal(button.dataset);
  });
});

modal.querySelectorAll(".js-close-modal").forEach(function (button) {
  button.addEventListener("click", function () {
    modal.close();
  });
});

// Clicking the dark area around the modal closes it too.
modal.addEventListener("click", function (event) {
  if (event.target === modal) {
    modal.close();
  }
});

// The server sends the form back with errors, so reopen it straight away.
if (modal.dataset.open === "true") {
  modal.showModal();
}

if (searchInput) {
  const rows = document.querySelectorAll(".js-client-row");
  const noResults = document.getElementById("no-results");

  searchInput.addEventListener("input", function () {
    const term = searchInput.value.trim().toLowerCase();
    let visible = 0;

    rows.forEach(function (row) {
      if (row.dataset.search.includes(term)) {
        row.hidden = false;
        visible++;
      } else {
        row.hidden = true;
      }
    });

    noResults.classList.toggle("is-hidden", visible > 0);
  });
}
