(() => {
  "use strict";

  const API = ""; // same-origin: sub-vendor workspace is served by the FastAPI app itself

  /* ----------------------------------------------------------
     State
  ---------------------------------------------------------- */
  const state = {
    expenses: [],
    categories: [],
    subcategories: [],
    paymentMethods: [],
    categoryRequests: [],
    subcategoryRequests: [],
    paymentReport: [],
    filters: { search: "", status: "", category: "" },
  };

  const PAYMENT_METHOD_FIELD_GROUPS = {
    cheque: ["cheque_number", "bank_name"],
  };

  /* ----------------------------------------------------------
     Small helpers
  ---------------------------------------------------------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const vendorId = () => Number(($("#vendorIdInput") || {}).value || window.Auth?.getVendorId() || 1);

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

  const fmtDateTime = (value) => {
    if (!value) return "—";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
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
    const opts = { ...options };
    if (opts.json !== undefined) {
      opts.headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
      opts.body = JSON.stringify(opts.json);
      delete opts.json;
    }
    opts.headers = { ...(window.Auth ? window.Auth.authHeader() : {}), ...(opts.headers || {}) };
    const res = await fetch(API + path, opts);
    if (res.status === 401) {
      // Session expired or invalid — send the vendor back to login.
      window.Auth?.logout();
      throw new Error("Session expired. Redirecting to sign in…");
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

  function escapeHtml(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ----------------------------------------------------------
     Navigation
  ---------------------------------------------------------- */
  const pageMeta = {
    dashboard: { title: "Dashboard", subtitle: "Overview of your submitted expenses." },
    expenses: { title: "Expenses", subtitle: "Every expense you've logged, filterable and actionable." },
    requests: { title: "Category requests", subtitle: "Ask the admin to add categories or subcategories you need." },
    reports: { title: "Payment report", subtitle: "Payouts made, broken down by payment method." },
    wallet: { title: "My Wallet", subtitle: "Your wallet balance and transaction history." },
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

  /* Keep the "Vendor ID" field and the expense form's created_by in sync */
  $("#vendorIdInput").addEventListener("input", () => {
    const input = $("#createdByInput");
    if (input) input.value = vendorId();
  });

  /* ----------------------------------------------------------
     Data loading
  ---------------------------------------------------------- */
  async function loadCategories() {
    state.categories = await api("/sub-vendor/categories");
    const selects = [$("#filterCategory"), $("#categorySelect"), $("#editCategorySelect")];
    selects.forEach((sel) => {
      if (!sel) return;
      const keepFirst = sel.id === "filterCategory" || sel.id === "categorySelect" ? sel.querySelector("option") : null;
      sel.innerHTML = "";
      if (keepFirst) sel.appendChild(keepFirst);
      state.categories.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.category_name;
        sel.appendChild(opt);
      });
    });

    const reqSel = $("#subcategoryRequestParentSelect");
    if (reqSel) {
      const keepFirst = reqSel.querySelector("option");
      reqSel.innerHTML = "";
      reqSel.appendChild(keepFirst);
      state.categories.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.category_name;
        reqSel.appendChild(opt);
      });
    }
  }

  async function loadPaymentMethods() {
    state.paymentMethods = await api("/sub-vendor/payment-methods");
    [$("#paymentMethodSelect"), $("#editPaymentMethodSelect")].forEach((select) => {
      if (!select) return;
      select.innerHTML = '<option value="">Select method</option>';
      state.paymentMethods.forEach((method) => {
        const opt = document.createElement("option");
        opt.value = method.payment_method_name;
        opt.textContent = method.payment_method_name;
        select.appendChild(opt);
      });
    });

    const filterSelect = $("#paymentMethodFilterSelect");
    if (filterSelect) {
      filterSelect.innerHTML = '<option value="">All payment methods</option>';
      state.paymentMethods.forEach((method) => {
        const opt = document.createElement("option");
        opt.value = method.id;
        opt.textContent = method.payment_method_name;
        filterSelect.appendChild(opt);
      });
    }
  }

  function setupPaymentMethodFields() {
    const paymentMethodSelect = $("#paymentMethodSelect");
    const paymentDetails = $("#paymentDetails");
    const chequeNumber = $("#chequeNumber");
    const bankName = $("#bankName");
    if (!paymentMethodSelect || !paymentDetails) return;

    paymentMethodSelect.addEventListener("change", () => {
      const method = paymentMethodSelect.value.trim().toLowerCase();
      const needsFields = PAYMENT_METHOD_FIELD_GROUPS[method];
      if (needsFields) {
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

  async function loadSubcategories(categoryId, selectId = "subcategorySelect") {
    const sel = $(`#${selectId}`);
    if (!sel) return;
    sel.innerHTML = '<option value="">Select subcategory</option>';
    if (!categoryId) return;
    const subs = await api(`/sub-vendor/categories/${categoryId}/subcategories`);
    subs.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = s.subcategory_name;
      sel.appendChild(opt);
    });
  }

  async function loadExpenses() {
    state.expenses = await api("/sub-vendor/expenses");
    renderExpenseTable();
    renderRecentActivity();
  }

  async function loadDashboard() {
    const summary = await api("/sub-vendor/dashboard");
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
  }

  async function loadCategoryRequests() {
    state.categoryRequests = await api(`/sub-vendor/category-requests?requested_by=${vendorId()}`);
    renderCategoryRequests();
  }

  async function loadSubcategoryRequests() {
    state.subcategoryRequests = await api(`/sub-vendor/subcategory-requests?requested_by=${vendorId()}`);
    renderSubcategoryRequests();
  }

  async function loadPaymentReport() {
    const filterSelect = $("#paymentMethodFilterSelect");
    const methodId = filterSelect ? filterSelect.value : "";
    const qs = methodId ? `?payment_method_id=${methodId}` : "";
    state.paymentReport = await api(`/sub-vendor/reports/payments${qs}`);
    renderPaymentReport();
  }

  async function refreshAll() {
    await Promise.all([
      loadCategories(),
      loadPaymentMethods(),
      loadExpenses(),
      loadDashboard(),
      loadReport(),
      loadCategoryRequests(),
      loadSubcategoryRequests(),
    ]);
    await loadPaymentReport();
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
      wrap.innerHTML = '<p class="empty-mini">No spend recorded yet.</p>';
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

  function statusBadge(status) {
    const cls = "badge-" + String(status).toLowerCase();
    return `<span class="badge ${cls}">${escapeHtml(status)}</span>`;
  }

  function requestStatusBadge(status) {
    const s = (status || "PENDING").toUpperCase();
    const cls = s === "APPROVED" ? "badge-approved" : s === "REJECTED" ? "badge-rejected" : "badge-pending";
    return `<span class="badge ${cls}">${escapeHtml(s)}</span>`;
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

  /* ----------------------------------------------------------
     Rendering — expenses table
  ---------------------------------------------------------- */
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
        ].join(" ").toLowerCase();
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

      // Sub-vendors can edit or withdraw an expense while it's still
      // awaiting admin review. Approve / reject / mark-paid live in
      // the admin panel.
      if (e.status === "Pending") {
        actions += `<button class="btn btn-ghost btn-sm" data-action="edit" data-id="${e.id}">Edit</button>`;
        actions += `<button class="btn btn-ghost btn-sm" data-action="withdraw" data-id="${e.id}">Withdraw</button>`;
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
      if (action === "withdraw") {
        await withdrawExpense(id);
      } else if (action === "receipt") {
        showReceipt(id);
      } else if (action === "edit") {
        openEditModal(id);
      }
    } catch (err) {
      toast(err.message || "Something went wrong", "error");
    }
  });

  async function withdrawExpense(id) {
    if (!confirm("Withdraw this expense? It will be marked as rejected and can't be resubmitted.")) return;
    await api(`/sub-vendor/expenses/${id}/reject`, {
      method: "PUT",
      json: { approved_by: vendorId(), remarks: "Withdrawn by sub-vendor" },
    });
    toast("Expense withdrawn", "success");
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
  function openModal(sel) { $(sel).classList.add("is-open"); }
  function closeModal(sel) { $(sel).classList.remove("is-open"); }

  $("#openAddExpense").addEventListener("click", () => {
    $("#expenseForm").reset();
    $("#modalTitle").textContent = "New expense";
    $("#subcategorySelect").innerHTML = '<option value="">Select subcategory</option>';
    $("#createdByInput").value = vendorId();
    const dateInput = $("#expenseForm [name=expense_date]");
    dateInput.value = new Date().toISOString().slice(0, 10);
    openModal("#modalBackdrop");
    Promise.all([loadCategories(), loadPaymentMethods()]).catch(() => {
      toast("Could not refresh categories or payment methods", "error");
    });
  });

  $("#closeModal").addEventListener("click", () => closeModal("#modalBackdrop"));
  $("#cancelModal").addEventListener("click", () => closeModal("#modalBackdrop"));
  $("#closeReceiptModal").addEventListener("click", () => closeModal("#receiptBackdrop"));
  $("#closeEditModal").addEventListener("click", () => closeModal("#editModalBackdrop"));
  $("#cancelEditModal").addEventListener("click", () => closeModal("#editModalBackdrop"));

  $$(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) backdrop.classList.remove("is-open");
    });
  });

  $("#categorySelect").addEventListener("change", (e) => {
    loadSubcategories(e.target.value, "subcategorySelect").catch(() => toast("Could not load subcategories", "error"));
  });
  $("#editCategorySelect").addEventListener("change", (e) => {
    loadSubcategories(e.target.value, "editSubcategorySelect").catch(() => toast("Could not load subcategories", "error"));
  });

  $("#expenseForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = $("#submitExpense");
    submitBtn.disabled = true;
    submitBtn.textContent = "Saving…";

    try {
      const formData = new FormData(e.target);
      if (!formData.get("subcategory_id")) formData.delete("subcategory_id");
      const receiptFile = formData.get("receipt");
      if (receiptFile instanceof File && receiptFile.size === 0) formData.delete("receipt");

      await api("/sub-vendor/expenses", { method: "POST", body: formData });
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
     Edit expense modal
  ---------------------------------------------------------- */
  let editTargetId = null;

  async function openEditModal(id) {
    const expense = state.expenses.find((e) => String(e.id) === String(id));
    if (!expense) return;
    editTargetId = id;

    await Promise.all([loadCategories(), loadPaymentMethods()]);
    if (expense.category) await loadSubcategories(expense.category.id, "editSubcategorySelect");

    const form = $("#editExpenseForm");
    form.title.value = expense.title;
    form.expense_date.value = expense.expense_date;
    form.category_id.value = expense.category ? expense.category.id : "";
    form.amount.value = expense.amount;
    form.payment_method.value = expense.payment_method;
    form.description.value = expense.description || "";
    form.remarks.value = expense.remarks || "";

    if (expense.subcategory) {
      setTimeout(() => { form.subcategory_id.value = expense.subcategory.id; }, 150);
    }

    openModal("#editModalBackdrop");
  }

  $("#editExpenseForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!editTargetId) return;
    const formData = new FormData(e.target);

    const payload = {
      title: formData.get("title"),
      expense_date: formData.get("expense_date"),
      category_id: Number(formData.get("category_id")),
      subcategory_id: formData.get("subcategory_id") ? Number(formData.get("subcategory_id")) : null,
      amount: formData.get("amount"),
      payment_method: formData.get("payment_method"),
      description: formData.get("description") || null,
      remarks: formData.get("remarks") || null,
    };

    try {
      await api(`/sub-vendor/expenses/${editTargetId}`, { method: "PUT", json: payload });
      toast("Expense updated", "success");
      closeModal("#editModalBackdrop");
      editTargetId = null;
      await Promise.all([loadExpenses(), loadDashboard(), loadReport()]);
    } catch (err) {
      toast(err.message || "Could not update expense", "error");
    }
  });

  /* ----------------------------------------------------------
     Category / subcategory requests
  ---------------------------------------------------------- */
  function renderCategoryRequests() {
    const body = $("#categoryRequestsTableBody");
    const empty = $("#categoryRequestsEmpty");
    if (state.categoryRequests.length === 0) {
      body.innerHTML = "";
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    body.innerHTML = state.categoryRequests
      .slice()
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      .map((r) => `
        <tr>
          <td class="cell-title">${escapeHtml(r.category_name)}</td>
          <td class="cell-reason">${escapeHtml(r.remarks || "—")}</td>
          <td>${requestStatusBadge(r.status)}</td>
          <td>${fmtDateTime(r.created_at)}</td>
          <td class="cell-reason muted">${escapeHtml(r.rejection_reason || "—")}</td>
        </tr>
      `).join("");
  }

  function renderSubcategoryRequests() {
    const body = $("#subcategoryRequestsTableBody");
    const empty = $("#subcategoryRequestsEmpty");
    if (state.subcategoryRequests.length === 0) {
      body.innerHTML = "";
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    const categoriesById = {};
    state.categories.forEach((c) => { categoriesById[c.id] = c; });

    body.innerHTML = state.subcategoryRequests
      .slice()
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      .map((r) => `
        <tr>
          <td class="cell-title">${escapeHtml(r.subcategory_name)}</td>
          <td>${escapeHtml((categoriesById[r.category_id] || {}).category_name || ("#" + r.category_id))}</td>
          <td class="cell-reason">${escapeHtml(r.remarks || "—")}</td>
          <td>${requestStatusBadge(r.status)}</td>
          <td>${fmtDateTime(r.created_at)}</td>
          <td class="cell-reason muted">${escapeHtml(r.rejection_reason || "—")}</td>
        </tr>
      `).join("");
  }

  $("#categoryRequestForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const name = (formData.get("category_name") || "").trim();
    if (!name) return;

    try {
      await api("/sub-vendor/category-requests", {
        method: "POST",
        json: { category_name: name, requested_by: vendorId(), remarks: formData.get("remarks") || null },
      });
      toast("Category request sent", "success");
      e.target.reset();
      await loadCategoryRequests();
    } catch (err) {
      toast(err.message || "Could not send request", "error");
    }
  });

  $("#subcategoryRequestForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const categoryId = Number(formData.get("category_id"));
    const name = (formData.get("subcategory_name") || "").trim();
    if (!categoryId || !name) return;

    try {
      await api("/sub-vendor/subcategory-requests", {
        method: "POST",
        json: {
          category_id: categoryId,
          subcategory_name: name,
          requested_by: vendorId(),
          remarks: formData.get("remarks") || null,
        },
      });
      toast("Subcategory request sent", "success");
      e.target.reset();
      await loadSubcategoryRequests();
    } catch (err) {
      toast(err.message || "Could not send request", "error");
    }
  });

  /* ----------------------------------------------------------
     Payment report
  ---------------------------------------------------------- */
  function renderPaymentReport() {
    const wrap = $("#paymentReportWrap");
    if (state.paymentReport.length === 0) {
      wrap.innerHTML = '<p class="empty-mini">No payments recorded yet.</p>';
      return;
    }
    const total = state.paymentReport.reduce((sum, r) => sum + Number(r.amount), 0);
    wrap.innerHTML = `
      <table class="report-table">
        <thead><tr><th>Expense</th><th>Payment method</th><th>Amount</th><th>Paid on</th></tr></thead>
        <tbody>
          ${state.paymentReport
            .map((r) => `
              <tr>
                <td>${escapeHtml(r.title)} <span class="cell-expense-num">${escapeHtml(r.expense_number)}</span></td>
                <td>${escapeHtml(r.payment_method_name)}</td>
                <td>${fmtMoney(r.amount)}</td>
                <td>${fmtDateTime(r.payment_date)}</td>
              </tr>
            `).join("")}
        </tbody>
        <tfoot>
          <tr><td colspan="2" style="font-weight:600;">Total</td><td style="font-family:var(--font-mono);font-weight:700;">${fmtMoney(total)}</td><td></td></tr>
        </tfoot>
      </table>
    `;
  }

  $("#paymentMethodFilterSelect").addEventListener("change", () => {
    loadPaymentReport().catch((err) => toast(err.message || "Could not load report", "error"));
  });

  /* ----------------------------------------------------------
     Init
  ---------------------------------------------------------- */
  // Prefill vendor identity from the logged-in session, if available.
  if (window.Auth?.isLoggedIn()) {
    const vid = window.Auth.getVendorId();
    const name = window.Auth.getName();
    if (vid) {
      const vendorInput = $("#vendorIdInput");
      const createdByInput = $("#createdByInput");
      if (vendorInput) vendorInput.value = vid;
      if (createdByInput) createdByInput.value = vid;
    }
    const userNameEl = $(".user-name");
    if (userNameEl && name) userNameEl.textContent = name;
  }

  $("#logoutBtn")?.addEventListener("click", () => window.Auth?.logout());

  setupPaymentMethodFields();
  refreshAll().catch((err) => {
    console.error(err);
    toast("Could not reach the API. Is the backend running?", "error");
  });
})();
