(() => {
  "use strict";

  const API = ""; // same-origin: frontend is served by the FastAPI app itself

  /* ----------------------------------------------------------
     State
  ---------------------------------------------------------- */
  const state = {
  expenses: [],
  categories: [],
  subcategories: [],
  paymentMethods: [],
  filters: { search: "", status: "", category: "" },
  currentUser: 1,
   };

  /* ----------------------------------------------------------
     Small helpers
  ---------------------------------------------------------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const fmtMoney = (value) => {
    const n = Number(value || 0);
    return "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 0 });
  };

  const fmtDate = (value) => {
    if (!value) return "—";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  };

  function toast(message, type = "default") {
    const stack = $("#toastStack");
    const el = document.createElement("div");
    el.className = "toast" + (type === "error" ? " toast-error" : type === "success" ? " toast-success" : "");
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(() => el.remove(), 3600);
  }

  async function api(path, options = {}) {
    const opts = { ...options, credentials: "same-origin" };
    if (opts.json !== undefined) {
      opts.headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
      opts.body = JSON.stringify(opts.json);
      delete opts.json;
    }
    const res = await fetch(API + path, opts);
    if (res.status === 401 && window.LedgerSession) {
      // Session cookie missing / expired / revoked server-side — bounce to login.
      window.LedgerSession.goToLogin();
      return new Promise(() => {}); // halt this call chain, we're navigating away
    }
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || JSON.stringify(body);
      } catch (_) { /* ignore */ }
      throw new Error(typeof detail === "string" ? detail : "Request failed");
    }
    if (res.status === 204) return null;
    return res.json();
  }

  /* ----------------------------------------------------------
     Navigation
  ---------------------------------------------------------- */
  const pageMeta = {
    dashboard: { title: "Dashboard", subtitle: "Overview of every rupee moving through the business." },
    expenses: { title: "Expenses", subtitle: "Every logged expense, filterable and actionable." },
    reports: { title: "Reports", subtitle: "Lifetime spend broken down by category." },
    wallet: { title: "Wallet", subtitle: "Your wallet balance and transaction history." },
  };

  function setView(view) {
    $$(".nav-item").forEach((btn) => btn.classList.toggle("is-active", btn.dataset.view === view));
    $$(".view").forEach((sec) => sec.classList.toggle("is-active", sec.id === `view-${view}`));
    const meta = pageMeta[view] || { title: "", subtitle: "" };
    $("#pageTitle").textContent = meta.title;
    $("#pageSubtitle").textContent = meta.subtitle;
    closeSidebar();
  }

  $$("[data-view]").forEach((el) => {
    el.addEventListener("click", () => setView(el.dataset.view));
  });

  /* mobile sidebar */
  function openSidebar() {
    $("#sidebar").classList.add("is-open");
    $("#scrim").classList.add("is-open");
  }
  function closeSidebar() {
    $("#sidebar").classList.remove("is-open");
    $("#scrim").classList.remove("is-open");
  }
  $("#hamburger").addEventListener("click", openSidebar);
  $("#scrim").addEventListener("click", closeSidebar);

  /* ----------------------------------------------------------
     Data loading
  ---------------------------------------------------------- */
  async function loadOptions() {
    // Real backend endpoint: GET /expenses/options returns
    // { categories, subcategories, payment_methods, employees } in one call.
    const options = await api("/expenses/options");
    state.categories = options.categories || [];
    state.subcategoriesAll = options.subcategories || [];
    state.paymentMethods = options.payment_methods || [];

    const catSelects = [$("#filterCategory"), $("#categorySelect")];
    catSelects.forEach((sel) => {
      const keepFirst = sel.querySelector("option");
      sel.innerHTML = "";
      sel.appendChild(keepFirst);
      state.categories.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.category_name;
        sel.appendChild(opt);
      });
    });
  }

  function setupPaymentMethodFields() {
  const paymentMethodSelect = $("select[name='payment_method']");
  const paymentDetails = $("#paymentDetails");

  const chequeNumber = $("#chequeNumber");
  const bankName = $("#bankName");

  if (!paymentMethodSelect || !paymentDetails) return;

  paymentMethodSelect.addEventListener("change", () => {
    const method = paymentMethodSelect.value
      .trim()
      .toLowerCase();

    if (method === "cheque") {

      paymentDetails.style.display = "grid";

      chequeNumber.required = true;
      bankName.required = true;

    } else {

      paymentDetails.style.display = "none";

      chequeNumber.required = false;
      bankName.required = false;

      chequeNumber.value = "";
      bankName.value = "";
    }
  });
}
  function loadSubcategories(categoryId) {
    // Subcategories come from the same /expenses/options payload —
    // there is no separate /expenses/categories/{id}/subcategories route.
    const sel = $("#subcategorySelect");
    sel.innerHTML = '<option value="">Select subcategory</option>';
    if (!categoryId) return;
    const subs = (state.subcategoriesAll || []).filter(
      (s) => String(s.category_id) === String(categoryId)
    );
    subs.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = s.subcategory_name;
      sel.appendChild(opt);
    });
  }

  async function loadExpenses() {
    state.expenses = await api("/expenses/");
    renderExpenseTable();
    renderRecentActivity();
  }

  async function loadDashboard() {
    const summary = await api("/dashboard/summary");
    $("#statTotalAmount").textContent = fmtMoney(summary.total_amount);
    $("#statTotalCount").textContent = summary.total_expenses;
    $("#statPending").textContent = summary.pending;
    $("#statApproved").textContent = summary.approved;
    $("#statRejected").textContent = summary.rejected;
    $("#statPaid").textContent = summary.paid;
  }

  async function loadReport() {
    const rows = await api("/reports/by-category");
    renderReportPanel(rows);
    renderReportTable(rows);
  }

  async function refreshAll() {
  await Promise.all([
    loadOptions(),
    loadExpenses(),
    loadDashboard(),
    loadReport()
  ]);
}

  /* ----------------------------------------------------------
     Rendering — dashboard
  ---------------------------------------------------------- */
  function renderReportPanel(rows) {
    const wrap = $("#categoryBars");
    wrap.innerHTML = "";
    const max = Math.max(1, ...rows.map((r) => Number(r.total_amount)));
    const nonZero = rows.filter((r) => Number(r.total_amount) > 0);

    if (nonZero.length === 0) {
      wrap.innerHTML = '<p class="empty-mini">No spend recorded yet. Log an expense to see the breakdown.</p>';
      return;
    }

    rows
      .slice()
      .sort((a, b) => Number(b.total_amount) - Number(a.total_amount))
      .forEach((r) => {
        const pct = Math.max(2, (Number(r.total_amount) / max) * 100);
        const row = document.createElement("div");
        row.className = "bar-row";
        row.innerHTML = `
          <span class="bar-name">${escapeHtml(r.category_name)}</span>
          <span class="bar-track"><span class="bar-fill" style="width:${pct}%"></span></span>
          <span class="bar-amount">${fmtMoney(r.total_amount)}</span>
        `;
        wrap.appendChild(row);
      });
  }

  function renderRecentActivity() {
    const wrap = $("#recentList");
    wrap.innerHTML = "";
    const recent = state.expenses.slice(0, 6);

    if (recent.length === 0) {
      wrap.innerHTML = '<p class="empty-mini">Nothing logged yet — add your first expense.</p>';
      return;
    }

    recent.forEach((e) => {
      const item = document.createElement("div");
      item.className = "recent-item";
      item.innerHTML = `
        <div class="recent-main">
          <div class="recent-title">${escapeHtml(e.title)}</div>
          <div class="recent-meta">${escapeHtml(e.expense_number)} · ${fmtDate(e.expense_date)}</div>
        </div>
        <div style="text-align:right;">
          <div class="recent-amount">${fmtMoney(e.amount)}</div>
          ${statusBadge(e.status)}
        </div>
      `;
      wrap.appendChild(item);
    });
  }

  function renderReportTable(rows) {
    const wrap = $("#reportTableWrap");
    if (rows.length === 0) {
      wrap.innerHTML = '<p class="empty-mini">No categories yet.</p>';
      return;
    }
    const total = rows.reduce((sum, r) => sum + Number(r.total_amount), 0);
    wrap.innerHTML = `
      <table class="report-table">
        <thead><tr><th>Category</th><th>Total spend</th></tr></thead>
        <tbody>
          ${rows
            .slice()
            .sort((a, b) => Number(b.total_amount) - Number(a.total_amount))
            .map((r) => `<tr><td>${escapeHtml(r.category_name)}</td><td>${fmtMoney(r.total_amount)}</td></tr>`)
            .join("")}
        </tbody>
        <tfoot>
          <tr><td style="font-weight:600;">Total</td><td style="font-family:var(--font-mono);font-weight:700;">${fmtMoney(total)}</td></tr>
        </tfoot>
      </table>
    `;
  }

  /* ----------------------------------------------------------
     Rendering — expenses table
  ---------------------------------------------------------- */
  function statusBadge(status) {
    const cls = "badge-" + status.toLowerCase();
    return `<span class="badge ${cls}">${status}</span>`;
  }

  function getFilteredExpenses() {
    const { search, status, category } = state.filters;
    const q = search.trim().toLowerCase();

    return state.expenses.filter((e) => {
      if (status && e.status !== status) return false;
      if (category && String(e.category_id) !== String(category)) return false;
      if (q) {
        const haystack = [
          e.title,
          e.expense_number,
          e.category ? e.category.category_name : "",
          e.description || "",
        ]
          .join(" ")
          .toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }

  function renderExpenseTable() {
    const rows = getFilteredExpenses();
    const body = $("#expenseTableBody");
    const empty = $("#emptyState");
    body.innerHTML = "";

    if (rows.length === 0) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;

    rows.forEach((e) => {
      const tr = document.createElement("tr");

      let actions = `<button class="btn btn-ghost btn-sm" data-action="receipt" data-id="${e.id}">Receipt</button>`;

      // Employees can only withdraw an expense while it's still awaiting
      // admin review. Approve / reject / mark-paid live in the admin panel.
      if (e.status === "Pending") {
        actions += `<button class="btn btn-ghost btn-sm" data-action="delete" data-id="${e.id}">Delete</button>`;
      }

      tr.innerHTML = `
        <td>
          <div class="cell-title">${escapeHtml(e.title)}</div>
          <span class="cell-expense-num">${escapeHtml(e.expense_number)}</span>
        </td>
        <td>${fmtDate(e.expense_date)}</td>
        <td>${e.category ? escapeHtml(e.category.category_name) : "—"}${e.subcategory ? ` <span class="muted">· ${escapeHtml(e.subcategory.subcategory_name)}</span>` : ""}</td>
        <td class="cell-amount">${fmtMoney(e.amount)}</td>
        <td>${escapeHtml(e.payment_method)}</td>
        <td>${statusBadge(e.status)}</td>
        <td class="col-actions"><div class="row-actions">${actions}</div></td>
      `;
      body.appendChild(tr);
    });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* filters */
  $("#searchInput").addEventListener("input", (e) => {
    state.filters.search = e.target.value;
    renderExpenseTable();
  });
  $("#filterStatus").addEventListener("change", (e) => {
    state.filters.status = e.target.value;
    renderExpenseTable();
  });
  $("#filterCategory").addEventListener("change", (e) => {
    state.filters.category = e.target.value;
    renderExpenseTable();
  });

  /* row actions (event delegation) */
  $("#expenseTableBody").addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const id = btn.dataset.id;
    const action = btn.dataset.action;

    try {
      if (action === "delete") {
        await deleteExpense(id);
      } else if (action === "receipt") {
        showReceipt(id);
      }
    } catch (err) {
      toast(err.message || "Something went wrong", "error");
    }
  });

  async function deleteExpense(id) {
    if (!confirm("Delete this expense? This can't be undone.")) return;
    await api(`/expenses/${id}`, { method: "DELETE" });
    toast("Expense deleted", "success");
    await Promise.all([loadExpenses(), loadDashboard(), loadReport()]);
  }

  function showReceipt(id) {
    const expense = state.expenses.find((e) => String(e.id) === String(id));
    const body = $("#receiptBody");
    if (expense && expense.receipt_image) {
      const mime = expense.receipt_type || "image/png";
      if (mime.includes("pdf")) {
        body.innerHTML = `<a class="btn btn-primary" href="data:${mime};base64,${expense.receipt_image}" download="${escapeHtml(expense.receipt_name || "receipt.pdf")}">Download PDF receipt</a>`;
      } else {
        body.innerHTML = `<img src="data:${mime};base64,${expense.receipt_image}" alt="Receipt for ${escapeHtml(expense.title)}">`;
      }
    } else {
      body.innerHTML = '<p class="receipt-empty">No receipt was attached to this expense.</p>';
    }
    openModal("#receiptBackdrop");
  }

  /* ----------------------------------------------------------
     Add expense modal
  ---------------------------------------------------------- */
  function openModal(sel) {
    $(sel).classList.add("is-open");
  }
  function closeModal(sel) {
    $(sel).classList.remove("is-open");
  }

  $("#openAddExpense").addEventListener("click", () => {
    $("#expenseForm").reset();
    $("#modalTitle").textContent = "New expense";
    $("#subcategorySelect").innerHTML = '<option value="">Select subcategory</option>';
    const dateInput = $("#expenseForm [name=expense_date]");
    dateInput.value = new Date().toISOString().slice(0, 10);
    openModal("#modalBackdrop");
    // Re-fetch in case an admin added a category/subcategory since page load.
    loadOptions().catch(() => {
      toast(
        "Could not refresh categories or payment methods",
        "error"
      );
    });
  });

  $("#closeModal").addEventListener("click", () => closeModal("#modalBackdrop"));
  $("#cancelModal").addEventListener("click", () => closeModal("#modalBackdrop"));
  $("#closeReceiptModal").addEventListener("click", () => closeModal("#receiptBackdrop"));

  $$(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) backdrop.classList.remove("is-open");
    });
  });

  $("#categorySelect").addEventListener("change", (e) => {
    loadSubcategories(e.target.value).catch(() => toast("Could not load subcategories", "error"));
  });

  $("#expenseForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = $("#submitExpense");
    submitBtn.disabled = true;
    submitBtn.textContent = "Saving…";

    try {
      const formData = new FormData(e.target);
      // Employee is identified server-side via the auth cookie for
      // *reading* their own data, but /expenses/ still requires created_by
      // in the body — fill it from the logged-in session, not a free field.
      const session = window.LedgerSession ? window.LedgerSession.getSession() : null;
      formData.set("created_by", session ? session.employee_id : state.currentUser);
      // subcategory_id may be empty — strip it so backend Optional[int] works
      if (!formData.get("subcategory_id")) formData.delete("subcategory_id");
      // receipt input with no file: strip so backend treats it as absent
      const receiptFile = formData.get("receipt");
      if (receiptFile instanceof File && receiptFile.size === 0) formData.delete("receipt");

      await api("/expenses/", { method: "POST", body: formData });
      toast("Expense saved", "success");
      closeModal("#modalBackdrop");
      await Promise.all([loadExpenses(), loadDashboard(), loadReport()]);
    } catch (err) {
      toast(err.message || "Could not save expense", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Save expense";
    }
  });

  /* ----------------------------------------------------------
     Init
  ---------------------------------------------------------- */
  (() => {
    const session = window.LedgerSession ? window.LedgerSession.getSession() : null;
    if (session) state.currentUser = session.employee_id;
  })();
  setupPaymentMethodFields();
  refreshAll().catch((err) => {
    console.error(err);
    toast("Could not reach the API. Is the backend running?", "error");
  });
})();
