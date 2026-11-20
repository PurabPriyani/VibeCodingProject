// Invoices page: pages, tabs and search all load without reloading the page.
// The server sends back just the table, and it's swapped into #invoice-results.
// The address bar is kept in sync, so refresh and the back button still work.

const results = document.getElementById("invoice-results");
const tabs = document.querySelectorAll("#invoice-tabs .tab");
const searchInput = document.getElementById("invoice-search");

let currentStatus = new URLSearchParams(window.location.search).get("status") || "all";
let searchTimer = null;
let lastRequest = 0;

function buildUrl(page) {
  const params = new URLSearchParams();
  params.set("status", currentStatus);

  const term = searchInput.value.trim();
  if (term) {
    params.set("q", term);
  }
  if (page && page > 1) {
    params.set("page", page);
  }
  return "?" + params.toString();
}

function highlightTab() {
  tabs.forEach(function (tab) {
    tab.classList.toggle("is-active", tab.dataset.status === currentStatus);
  });
}

function loadResults(url, addToHistory) {
  // If the user clicks quickly, only the newest response is shown.
  lastRequest++;
  const thisRequest = lastRequest;

  results.classList.add("is-loading");

  fetch(url, { headers: { "X-Requested-With": "fetch" } })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("Server returned " + response.status);
      }
      return response.text();
    })
    .then(function (html) {
      if (thisRequest !== lastRequest) {
        return;
      }
      results.innerHTML = html;
      results.classList.remove("is-loading");

      if (addToHistory) {
        history.pushState(null, "", url);
      }

      // Bring the top of the table into view when moving between pages.
      const top = results.getBoundingClientRect().top;
      if (top < 0) {
        results.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    })
    .catch(function () {
      // Something went wrong with the quick update, so fall back to a normal page load.
      window.location.href = url;
    });
}

// Page numbers and arrows. The links are replaced every time, so the click is
// caught on the container instead of on each link.
results.addEventListener("click", function (event) {
  const link = event.target.closest("a.page-link");
  if (!link) {
    return;
  }
  event.preventDefault();
  loadResults(link.getAttribute("href"), true);
});

tabs.forEach(function (tab) {
  tab.addEventListener("click", function (event) {
    event.preventDefault();
    currentStatus = tab.dataset.status;
    highlightTab();
    loadResults(buildUrl(1), true);
  });
});

// Wait until the user stops typing for a moment before searching.
searchInput.addEventListener("input", function () {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(function () {
    loadResults(buildUrl(1), true);
  }, 300);
});

// Back and forward buttons.
window.addEventListener("popstate", function () {
  const params = new URLSearchParams(window.location.search);
  currentStatus = params.get("status") || "all";
  searchInput.value = params.get("q") || "";
  highlightTab();
  loadResults(window.location.search || "?", false);
});
