const STORAGE_KEY = "expense_tracker_v3_transactions";
const BUDGET_KEY = "expense_tracker_v3_budget";

const expenseCategories = [
  "Food",
  "Travel",
  "Shopping",
  "Education",
  "Bills",
  "Health",
  "Entertainment",
  "Other"
];

const incomeCategories = [
  "Salary",
  "Freelance",
  "Other"
];

const chartColors = [
  "#D9A441",
  "#6C9FC7",
  "#5FBA78",
  "#D86655",
  "#B28D5B",
  "#8A9A9E",
  "#C27BA0",
  "#7FA67B"
];

let transactions = [];
let editingId = null;

const $ = id => document.getElementById(id);

const money = value =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2
  }).format(Number(value) || 0);

const today = () =>
  new Date().toISOString().slice(0, 10);

const currentMonth = () =>
  today().slice(0, 7);

const escapeHTML = value =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

function loadTransactions() {
  try {
    return JSON.parse(
      localStorage.getItem(STORAGE_KEY)
    ) || [];
  } catch {
    return [];
  }
}

function saveTransactions() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(transactions)
  );
}

transactions = loadTransactions();

function formatDate(value) {
  return new Date(`${value}T00:00:00`)
    .toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric"
    });
}

function updateCategories(type = $("formType").value) {
  const categories =
    type === "Income"
      ? incomeCategories
      : expenseCategories;

  const current =
    $("formCategory").value;

  $("formCategory").innerHTML =
    categories
      .map(
        category =>
          `<option value="${escapeHTML(category)}">${escapeHTML(category)}</option>`
      )
      .join("");

  if (categories.includes(current)) {
    $("formCategory").value = current;
  }
}

function updateFilterOptions() {
  const months = [
    ...new Set(
      transactions.map(
        item => item.date.slice(0, 7)
      )
    )
  ].sort().reverse();

  const oldMonth =
    $("monthFilter").value;

  $("monthFilter").innerHTML =
    `<option value="all">All months</option>`;

  months.forEach(month => {
    const option =
      document.createElement("option");

    option.value = month;

    option.textContent =
      new Date(`${month}-01T00:00:00`)
        .toLocaleDateString("en-IN", {
          month: "long",
          year: "numeric"
        });

    $("monthFilter").appendChild(option);
  });

  $("monthFilter").value =
    months.includes(oldMonth)
      ? oldMonth
      : "all";

  const categories = [
    ...new Set(
      transactions.map(
        item => item.category
      )
    )
  ].sort();

  const oldCategory =
    $("categoryFilter").value;

  $("categoryFilter").innerHTML =
    `<option value="all">All categories</option>` +
    categories
      .map(
        category =>
          `<option value="${escapeHTML(category)}">${escapeHTML(category)}</option>`
      )
      .join("");

  $("categoryFilter").value =
    categories.includes(oldCategory)
      ? oldCategory
      : "all";
}

function getFilteredTransactions() {
  const search =
    $("searchInput")
      .value
      .trim()
      .toLowerCase();

  const month =
    $("monthFilter").value;

  const type =
    $("typeFilter").value;

  const category =
    $("categoryFilter").value;

  return transactions
    .filter(item => {
      if (
        month !== "all" &&
        item.date.slice(0, 7) !== month
      ) {
        return false;
      }

      if (
        type !== "all" &&
        item.type !== type
      ) {
        return false;
      }

      if (
        category !== "all" &&
        item.category !== category
      ) {
        return false;
      }

      if (search) {
        const text = [
          item.date,
          item.type,
          item.category,
          item.note
        ]
          .join(" ")
          .toLowerCase();

        if (!text.includes(search)) {
          return false;
        }
      }

      return true;
    })
    .sort((a, b) => {
      if (a.date === b.date) {
        return b.createdAt - a.createdAt;
      }

      return b.date.localeCompare(a.date);
    });
}

function renderTransactions() {
  const rows =
    getFilteredTransactions();

  const body =
    $("transactionBody");

  body.innerHTML = "";

  rows.forEach(item => {
    const row =
      document.createElement("tr");

    const amountClass =
      item.type === "Income"
        ? "amount-income"
        : "amount-expense";

    const sign =
      item.type === "Income"
        ? "+"
        : "−";

    row.innerHTML = `
      <td>${escapeHTML(formatDate(item.date))}</td>

      <td>
        <span class="type-pill ${item.type.toLowerCase()}">
          ${escapeHTML(item.type)}
        </span>
      </td>

      <td>${escapeHTML(item.category)}</td>

      <td class="${amountClass}">
        ${sign}${money(item.amount)}
      </td>

      <td>
        ${escapeHTML(item.note || "—")}
      </td>

      <td>
        <div class="row-actions">
          <button
            data-action="edit"
            data-id="${item.id}">
            Edit
          </button>

          <button
            class="delete"
            data-action="delete"
            data-id="${item.id}">
            Delete
          </button>
        </div>
      </td>
    `;

    body.appendChild(row);
  });

  $("emptyState")
    .classList
    .toggle(
      "show",
      rows.length === 0
    );
}

function updateSummary() {
  const income =
    transactions
      .filter(
        item => item.type === "Income"
      )
      .reduce(
        (sum, item) =>
          sum + Number(item.amount),
        0
      );

  const expenses =
    transactions
      .filter(
        item => item.type === "Expense"
      )
      .reduce(
        (sum, item) =>
          sum + Number(item.amount),
        0
      );

  const thisMonth =
    transactions
      .filter(
        item =>
          item.type === "Expense" &&
          item.date.slice(0, 7) ===
            currentMonth()
      )
      .reduce(
        (sum, item) =>
          sum + Number(item.amount),
        0
      );

  $("totalIncome").textContent =
    money(income);

  $("totalExpenses").textContent =
    money(expenses);

  $("currentBalance").textContent =
    money(income - expenses);

  $("monthExpenses").textContent =
    money(thisMonth);

  $("monthLabel").textContent =
    new Date(
      `${currentMonth()}-01T00:00:00`
    ).toLocaleDateString("en-IN", {
      month: "long",
      year: "numeric"
    });
}

function getSelectedMonth() {
  const value =
    $("monthFilter").value;

  return value === "all"
    ? currentMonth()
    : value;
}

function updateBudget() {
  const budget =
    Number(
      localStorage.getItem(
        BUDGET_KEY
      )
    ) || 0;

  const month =
    getSelectedMonth();

  const spent =
    transactions
      .filter(
        item =>
          item.type === "Expense" &&
          item.date.slice(0, 7) === month
      )
      .reduce(
        (sum, item) =>
          sum + Number(item.amount),
        0
      );

  $("budgetInput").value =
    budget || "";

  $("budgetSpent").textContent =
    money(spent);

  $("budgetRemaining").textContent =
    money(budget - spent);

  if (!budget) {
    $("budgetProgress").style.width =
      "0%";

    $("budgetProgress").style.background =
      "var(--gold)";

    $("budgetStatus").textContent =
      "Set a budget to track your monthly progress.";

    return;
  }

  const percentage =
    Math.min(
      (spent / budget) * 100,
      100
    );

  const remaining =
    budget - spent;

  $("budgetProgress").style.width =
    `${percentage}%`;

  if (remaining >= 0) {
    $("budgetProgress").style.background =
      "var(--gold)";

    $("budgetStatus").textContent =
      `${Math.round(percentage)}% used • ${money(remaining)} remaining`;
  } else {
    $("budgetProgress").style.background =
      "var(--red)";

    $("budgetStatus").textContent =
      `Budget exceeded by ${money(
        Math.abs(remaining)
      )}`;
  }
}

function updateAnalytics() {
  const month =
    getSelectedMonth();

  const rows =
    transactions.filter(
      item =>
        item.type === "Expense" &&
        item.date.slice(0, 7) === month
    );

  const total =
    rows.reduce(
      (sum, item) =>
        sum + Number(item.amount),
      0
    );

  const categories = {};

  rows.forEach(item => {
    categories[item.category] =
      (categories[item.category] || 0) +
      Number(item.amount);
  });

  const sorted =
    Object.entries(categories)
      .sort(
        (a, b) => b[1] - a[1]
      );

  const largest =
    rows.length
      ? Math.max(
          ...rows.map(
            item => Number(item.amount)
          )
        )
      : 0;

  const average =
    rows.length
      ? total / rows.length
      : 0;

  $("insightCount").textContent =
    rows.length;

  $("insightTop").textContent =
    sorted[0]?.[0] || "None";

  $("insightLargest").textContent =
    largest
      ? money(largest)
      : "₹0.00";

  $("insightAverage").textContent =
    average
      ? money(average)
      : "₹0.00";

  drawChart(
    sorted,
    total
  );
}

function drawChart(sorted, total) {
  const canvas =
    $("donutChart");

  const ctx =
    canvas.getContext("2d");

  const center = 130;
  const radius = 88;

  ctx.clearRect(
    0,
    0,
    canvas.width,
    canvas.height
  );

  if (!total) {
    ctx.beginPath();

    ctx.arc(
      center,
      center,
      radius,
      0,
      Math.PI * 2
    );

    ctx.strokeStyle =
      "#292d2e";

    ctx.lineWidth = 31;

    ctx.stroke();

    $("chartCenter")
      .querySelector("strong")
      .textContent = "₹0";

    $("chartCenter")
      .querySelector("span")
      .textContent = "expenses";

    $("legend").innerHTML = `
      <div class="legend-row">
        <span
          class="legend-dot"
          style="background:#45494a">
        </span>

        <span>No data yet</span>

        <strong>—</strong>
      </div>
    `;

    return;
  }

  let start =
    -Math.PI / 2;

  sorted.forEach(
    ([category, amount], index) => {
      const slice =
        (amount / total) *
        Math.PI *
        2;

      ctx.beginPath();

      ctx.arc(
        center,
        center,
        radius,
        start,
        start + slice
      );

      ctx.strokeStyle =
        chartColors[
          index %
            chartColors.length
        ];

      ctx.lineWidth = 31;

      ctx.stroke();

      start += slice;
    }
  );

  $("chartCenter")
    .querySelector("strong")
    .textContent =
    money(total)
      .replace(".00", "");

  $("chartCenter")
    .querySelector("span")
    .textContent =
    "expenses";

  $("legend").innerHTML =
    sorted
      .slice(0, 7)
      .map(
        ([category, amount], index) => `
          <div class="legend-row">

            <span
              class="legend-dot"
              style="background:${
                chartColors[
                  index %
                    chartColors.length
                ]
              }">
            </span>

            <span>
              ${escapeHTML(category)}
            </span>

            <strong>
              ${money(amount)}
            </strong>

          </div>
        `
      )
      .join("");
}

function openModal(id = null) {
  editingId = id;

  $("modal")
    .classList
    .remove("hidden");

  if (id) {
    const item =
      transactions.find(
        transaction =>
          transaction.id === id
      );

    if (!item) {
      closeModal();
      return;
    }

    $("modalTitle").textContent =
      "Edit transaction";

    $("dateInput").value =
      item.date;

    $("formType").value =
      item.type;

    updateCategories(
      item.type
    );

    $("formCategory").value =
      item.category;

    $("amountInput").value =
      item.amount;

    $("noteInput").value =
      item.note || "";
  } else {
    $("modalTitle").textContent =
      "Add transaction";

    $("dateInput").value =
      today();

    $("formType").value =
      "Expense";

    updateCategories(
      "Expense"
    );

    $("formCategory").value =
      "Food";

    $("amountInput").value =
      "";

    $("noteInput").value =
      "";
  }

  setTimeout(
    () =>
      $("amountInput").focus(),
    50
  );
}

function closeModal() {
  $("modal")
    .classList
    .add("hidden");

  editingId = null;
}

function submitTransaction(event) {
  event.preventDefault();

  const date =
    $("dateInput").value;

  const type =
    $("formType").value;

  const category =
    $("formCategory").value;

  const amount =
    Number(
      $("amountInput").value
    );

  const note =
    $("noteInput")
      .value
      .trim();

  if (
    !date ||
    !type ||
    !category ||
    !amount ||
    amount <= 0
  ) {
    alert(
      "Please enter valid transaction details."
    );

    return;
  }

  if (editingId) {
    const index =
      transactions.findIndex(
        item =>
          item.id ===
          editingId
      );

    if (index !== -1) {
      transactions[index] = {
        ...transactions[index],
        date,
        type,
        category,
        amount,
        note
      };
    }
  } else {
    transactions.push({
      id:
        crypto.randomUUID
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random()}`,

      date,
      type,
      category,
      amount,
      note,

      createdAt:
        Date.now()
    });
  }

  saveTransactions();

  closeModal();

  renderAll();
}

function deleteTransaction(id) {
  const item =
    transactions.find(
      transaction =>
        transaction.id === id
    );

  if (!item) {
    return;
  }

  const confirmed =
    confirm(
      `Delete this ${item.type.toLowerCase()} of ${money(item.amount)}?`
    );

  if (!confirmed) {
    return;
  }

  transactions =
    transactions.filter(
      transaction =>
        transaction.id !== id
    );

  saveTransactions();

  renderAll();
}

function clearAllData() {
  if (!transactions.length) {
    alert(
      "There are no transactions to clear."
    );

    return;
  }

  const confirmed =
    confirm(
      "This will permanently remove all transactions from this browser. Continue?"
    );

  if (!confirmed) {
    return;
  }

  transactions = [];

  localStorage.removeItem(
    STORAGE_KEY
  );

  renderAll();
}

function exportCSV() {
  if (!transactions.length) {
    alert(
      "There are no transactions to export."
    );

    return;
  }

  const rows = [
    [
      "Date",
      "Type",
      "Category",
      "Amount",
      "Note"
    ]
  ];

  transactions.forEach(item => {
    rows.push([
      item.date,
      item.type,
      item.category,
      item.amount,
      item.note || ""
    ]);
  });

  const csv =
    rows
      .map(row =>
        row
          .map(
            value =>
              `"${String(value)
                .replaceAll(
                  '"',
                  '""'
                )}"`
          )
          .join(",")
      )
      .join("\n");

  const blob =
    new Blob(
      [csv],
      {
        type:
          "text/csv;charset=utf-8"
      }
    );

  const url =
    URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;

  link.download =
    "expense-tracker-transactions.csv";

  document.body.appendChild(link);

  link.click();

  link.remove();

  URL.revokeObjectURL(url);
}

function parseCSV(text) {
  const rows = [];

  let row = [];
  let value = "";
  let quoted = false;

  for (
    let i = 0;
    i < text.length;
    i++
  ) {
    const char =
      text[i];

    const next =
      text[i + 1];

    if (
      char === '"' &&
      quoted &&
      next === '"'
    ) {
      value += '"';
      i++;
    } else if (
      char === '"'
    ) {
      quoted = !quoted;
    } else if (
      char === "," &&
      !quoted
    ) {
      row.push(value);
      value = "";
    } else if (
      (char === "\n" ||
        char === "\r") &&
      !quoted
    ) {
      if (
        char === "\r" &&
        next === "\n"
      ) {
        i++;
      }

      row.push(value);

      rows.push(row);

      row = [];

      value = "";
    } else {
      value += char;
    }
  }

  if (
    value ||
    row.length
  ) {
    row.push(value);
    rows.push(row);
  }

  return rows.filter(
    currentRow =>
      currentRow.some(
        cell => cell !== ""
      )
  );
}

function importCSV(file) {
  const reader =
    new FileReader();

  reader.onload = () => {
    const rows =
      parseCSV(
        reader.result
      );

    if (rows.length < 2) {
      alert(
        "The CSV does not contain transaction rows."
      );

      return;
    }

    const headers =
      rows[0].map(
        header =>
          header
            .trim()
            .toLowerCase()
      );

    const required = [
      "date",
      "type",
      "category",
      "amount",
      "note"
    ];

    if (
      !required.every(
        key =>
          headers.includes(key)
      )
    ) {
      alert(
        "CSV must contain Date, Type, Category, Amount and Note columns."
      );

      return;
    }

    const imported = [];

    rows
      .slice(1)
      .forEach(row => {
        const item = {};

        headers.forEach(
          (header, index) => {
            item[header] =
              row[index] || "";
          }
        );

        const amount =
          Number(item.amount);

        const validDate =
          /^\d{4}-\d{2}-\d{2}$/
            .test(item.date);

        const validType =
          ["Income", "Expense"]
            .includes(item.type);

        if (
          validDate &&
          validType &&
          item.category &&
          amount > 0
        ) {
          imported.push({
            id:
              crypto.randomUUID
                ? crypto.randomUUID()
                : `${Date.now()}-${Math.random()}`,

            date:
              item.date,

            type:
              item.type,

            category:
              item.category,

            amount,

            note:
              item.note || "",

            createdAt:
              Date.now()
          });
        }
      });

    if (!imported.length) {
      alert(
        "No valid transactions were found in the CSV."
      );

      return;
    }

    transactions.push(
      ...imported
    );

    saveTransactions();

    renderAll();

    alert(
      `${imported.length} transaction(s) imported successfully.`
    );
  };

  reader.readAsText(file);
}

function saveBudget() {
  const value =
    Number(
      $("budgetInput").value
    );

  if (
    !value ||
    value <= 0
  ) {
    localStorage.removeItem(
      BUDGET_KEY
    );
  } else {
    localStorage.setItem(
      BUDGET_KEY,
      String(value)
    );
  }

  updateBudget();
}

function renderAll() {
  updateFilterOptions();
  renderTransactions();
  updateSummary();
  updateBudget();
  updateAnalytics();
}

$("transactionForm")
  .addEventListener(
    "submit",
    submitTransaction
  );

$("addBtn")
  .addEventListener(
    "click",
    () => openModal()
  );

$("addTopBtn")
  .addEventListener(
    "click",
    () => openModal()
  );

$("emptyAddBtn")
  .addEventListener(
    "click",
    () => openModal()
  );

$("closeModalBtn")
  .addEventListener(
    "click",
    closeModal
  );

$("cancelBtn")
  .addEventListener(
    "click",
    closeModal
  );

$("modalBackdrop")
  .addEventListener(
    "click",
    closeModal
  );

$("formType")
  .addEventListener(
    "change",
    () =>
      updateCategories(
        $("formType").value
      )
  );

$("transactionBody")
  .addEventListener(
    "click",
    event => {
      const button =
        event.target.closest(
          "button[data-action]"
        );

      if (!button) {
        return;
      }

      const id =
        button.dataset.id;

      const action =
        button.dataset.action;

      if (
        action === "edit"
      ) {
        openModal(id);
      }

      if (
        action === "delete"
      ) {
        deleteTransaction(id);
      }
    }
  );

[
  $("searchInput"),
  $("monthFilter"),
  $("typeFilter"),
  $("categoryFilter")
].forEach(element => {
  element.addEventListener(
    "input",
    renderAll
  );

  element.addEventListener(
    "change",
    renderAll
  );
});

$("saveBudgetBtn")
  .addEventListener(
    "click",
    saveBudget
  );

$("exportBtn")
  .addEventListener(
    "click",
    exportCSV
  );

$("importBtn")
  .addEventListener(
    "click",
    () =>
      $("csvInput").click()
  );

$("csvInput")
  .addEventListener(
    "change",
    event => {
      const file =
        event.target.files[0];

      if (file) {
        importCSV(file);
      }

      event.target.value = "";
    }
  );

$("clearAllBtn")
  .addEventListener(
    "click",
    clearAllData
  );

document.addEventListener(
  "keydown",
  event => {
    if (
      event.key === "Escape" &&
      !$("modal")
        .classList
        .contains("hidden")
    ) {
      closeModal();
    }

    if (
      event.ctrlKey &&
      event.key.toLowerCase() === "n"
    ) {
      event.preventDefault();
      openModal();
    }

    if (
      event.ctrlKey &&
      event.key.toLowerCase() === "f"
    ) {
      event.preventDefault();
      $("searchInput").focus();
    }
  }
);

document
  .querySelectorAll(
    ".nav-item"
  )
  .forEach(button => {
    button.addEventListener(
      "click",
      () => {
        const target =
          document.getElementById(
            button.dataset.scroll
          );

        if (target) {
          target.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });
        }

        document
          .querySelectorAll(
            ".nav-item"
          )
          .forEach(item =>
            item.classList.remove(
              "active"
            )
          );

        button.classList.add(
          "active"
        );
      }
    );
  });

updateCategories("Expense");

renderAll();