(() => {
  "use strict";

  const API = ""; // same-origin: admin panel is served by the FastAPI app itself

  /* ----------------------------------------------------------
     State
  ---------------------------------------------------------- */
  const state = {
    pending: [],
    approved: [],
    rejected: [],
    paid: [],
    reportRows: [],
    paymentMethods: [],
    paymentMethodReport: [],
    categories: [],
    subcategories: [],
  };

  /* Payment methods that require the same extra details as the backend
     validates in crud.mark_as_paid — keep these groups in sync with it. */
  const PAYMENT_METHOD_FIELD_GROUPS = {
    cheque: ["cheque_number", "bank_name"],
    "debit card": ["account_last_four", "transaction_reference"],
    "credit card": ["account_last_four", "transaction_reference"],
    "corporate card": ["account_last_four", "transaction_reference"],
    upi: ["transaction_reference"],
    "google pay": ["transaction_reference"],
    phonepe: ["transaction_reference"],
    "amazon pay": ["transaction_reference"],
    "paytm wallet": ["transaction_reference"],
    "bank account": ["bank_name", "account_last_four", "transaction_reference"],
    "bank transfer": ["bank_name", "account_last_four", "transaction_reference"],
    "net banking": ["bank_name", "account_last_four", "transaction_reference"],
    neft: ["bank_name", "account_last_four", "transaction_reference"],
    rtgs: ["bank_name", "account_last_four", "transaction_reference"],
    imps: ["bank_name", "account_last_four", "transaction_reference"],
  };

  /* ----------------------------------------------------------
     Small helpers
  ---------------------------------------------------------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const adminId = () => Number($("#adminIdInput").value || 1);

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
    const res = await fetch(API + path, opts);
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
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ----------------------------------------------------------
     Navigation
  ---------------------------------------------------------- */
  const pageMeta = {
    dashboard: { title: "Dashboard", subtitle: "Company-wide expense activity at a glance." },
    pending: { title: "Pending approvals", subtitle: "Review, approve or reject incoming expense claims." },
    approved: { title: "Approved · awaiting payout", subtitle: "Approved expenses ready to be marked as paid." },
    paid: { title: "Paid", subtitle: "Full history of settled expenses." },
    rejected: { title: "Rejected", subtitle: "Declined claims and the reasons given." },
    reports: { title: "Reports", subtitle: "Lifetime spend broken down by category." },
    wallet: { title: "Wallet", subtitle: "Look up balances and manage credits/debits for employees and sub-vendors." },
    categories: { title: "Categories", subtitle: "Manage expense categories, subcategories, and payment methods." },
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
  $("#refreshBtn").addEventListener("click", () => refreshAll().catch(() => toast("Could not refresh", "error")));

  /* ----------------------------------------------------------
     Data loading
  ---------------------------------------------------------- */
  async function loadDashboard() {
    const summary = await api("/admin/dashboard");
    $("#statTotalAmount").textContent = fmtMoney(summary.total_amount);
    $("#statTotalCount").textContent = summary.total_expenses;
    $("#statPending").textContent = summary.pending;
    $("#statApproved").textContent = summary.approved;
    $("#statRejected").textContent = summary.rejected;
    $("#statPaid").textContent = summary.paid;
    $("#navPendingCount").textContent = summary.pending;
  }

  async function loadPending() {
    state.pending = await api("/admin/expenses/pending");
    renderPendingTable();
    renderRecentAttention();
  }

  async function loadApproved() {
    state.approved = await api("/admin/expenses/approved");
    renderApprovedTable();
  }

  async function loadRejected() {
    state.rejected = await api("/admin/expenses/rejected");
    renderRejectedTable();
  }

  async function loadPaid() {
    state.paid = await api("/admin/expenses/paid");
    renderPaidTable();
  }

  async function loadReport() {
    state.reportRows = await api("/reports/by-category");
    renderReportPanel(state.reportRows);
    renderReportTable(state.reportRows);
  }

  async function loadPaymentMethodReport() {
    state.paymentMethodReport = await api("/admin/reports/payment-methods");
    const filterSelect = $("#paymentMethodFilterSelect");
    renderPaymentMethodDetail(filterSelect ? filterSelect.value : "");
  }

  async function loadPaymentMethods() {
    state.paymentMethods = await api("/admin/payment-methods");
    renderPaymentMethodOptions();
    renderPaymentMethodFilterOptions();
    renderPaymentMethodList();
  }

  async function loadCategories() {
    const [categories, subcategories] = await Promise.all([
      api("/expenses/categories"),
      api("/expenses/subcategories"),
    ]);
    state.categories = categories;
    state.subcategories = subcategories;
    renderCategoryParentOptions();
    renderCategoryList();
  }

  async function refreshAll() {
    await Promise.all([
      loadDashboard(),
      loadPending(),
      loadApproved(),
      loadRejected(),
      loadPaid(),
      loadReport(),
      loadPaymentMethodReport(),
      loadPaymentMethods(),
      loadCategories(),
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

  function renderRecentAttention() {
    const wrap = $("#recentList");
    wrap.innerHTML = "";
    const recent = state.pending.slice(0, 6);

    if (recent.length === 0) {
      wrap.innerHTML = '<p class="empty-mini">Nothing waiting on you right now.</p>';
      return;
    }

    recent.forEach((e) => {
      const item = document.createElement("div");
      item.className = "recent-item";
      item.innerHTML = `
        <div class="recent-main">
          <div class="recent-title">${escapeHtml(e.title)}</div>
          <div class="recent-meta">${escapeHtml(e.expense_number)} · Employee #${e.created_by} · ${fmtDate(e.expense_date)}</div>
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

  function renderPaymentMethodReportTable(rows) {
    const wrap = $("#paymentMethodReportWrap");
    if (!rows || rows.length === 0) {
      wrap.innerHTML = '<p class="empty-mini">No payouts recorded yet.</p>';
      return;
    }
    const total = rows.reduce((sum, r) => sum + Number(r.total_amount), 0);
    wrap.innerHTML = `
      <table class="report-table">
        <thead><tr><th>Payment method</th><th>Payments</th><th>Total paid</th></tr></thead>
        <tbody>
          ${rows
            .slice()
            .sort((a, b) => Number(b.total_amount) - Number(a.total_amount))
            .map(
              (r) =>
                `<tr><td>${escapeHtml(r.payment_method_name)}</td><td>${r.payment_count}</td><td>${fmtMoney(r.total_amount)}</td></tr>`
            )
            .join("")}
        </tbody>
        <tfoot>
          <tr><td style="font-weight:600;">Total</td><td></td><td style="font-family:var(--font-mono);font-weight:700;">${fmtMoney(total)}</td></tr>
        </tfoot>
      </table>
    `;
  }

  function renderPaymentMethodFilterOptions() {
    const select = $("#paymentMethodFilterSelect");
    const current = select.value;
    select.innerHTML = '<option value="">All payment methods</option>' +
      state.paymentMethods
        .slice()
        .sort((a, b) => a.payment_method_name.localeCompare(b.payment_method_name))
        .map((m) => `<option value="${m.id}">${escapeHtml(m.payment_method_name)}</option>`)
        .join("");
    select.value = current;
  }

  async function renderPaymentMethodDetail(methodId) {
    const wrap = $("#paymentMethodReportWrap");

    if (!methodId) {
      renderPaymentMethodReportTable(state.paymentMethodReport);
      return;
    }

    wrap.innerHTML = '<p class="empty-mini">Loading&hellip;</p>';

    try {
      const rows = await api(`/admin/payment-methods/${methodId}/details`);

      if (rows.length === 0) {
        wrap.innerHTML = '<p class="empty-mini">No payments recorded for this method yet.</p>';
        return;
      }

      wrap.innerHTML = `
        <table class="report-table">
          <thead>
            <tr>
              <th>Expense</th>
              <th>Paid</th>
              <th>Cheque no.</th>
              <th>Bank</th>
              <th>Account</th>
              <th>Reference</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            ${rows
              .map(
                (r) => `
              <tr>
                <td>${escapeHtml(r.title)} <span class="muted">(${escapeHtml(r.expense_number)})</span></td>
                <td class="cell-meta">${fmtDateTime(r.payment_date)}</td>
                <td>${r.cheque_number ? escapeHtml(r.cheque_number) : "—"}</td>
                <td>${r.bank_name ? escapeHtml(r.bank_name) : "—"}</td>
                <td>${r.account_last_four ? "&bull;&bull;&bull;&bull; " + escapeHtml(r.account_last_four) : "—"}</td>
                <td>${r.transaction_reference ? escapeHtml(r.transaction_reference) : "—"}</td>
                <td>${fmtMoney(r.amount)}</td>
              </tr>
            `
              )
              .join("")}
          </tbody>
          <tfoot>
            <tr>
              <td style="font-weight:600;" colspan="6">Total (${rows.length} payment${rows.length === 1 ? "" : "s"})</td>
              <td style="font-family:var(--font-mono);font-weight:700;">${fmtMoney(rows.reduce((sum, r) => sum + Number(r.amount), 0))}</td>
            </tr>
          </tfoot>
        </table>
      `;
    } catch (err) {
      wrap.innerHTML = `<p class="empty-mini">Could not load details: ${escapeHtml(err.message || "unknown error")}</p>`;
    }
  }

  $("#paymentMethodFilterSelect").addEventListener("change", (e) => {
    renderPaymentMethodDetail(e.target.value);
  });

  /* ----------------------------------------------------------
     Payment report by period (daily / weekly / monthly / custom)
     Backed by GET /admin/payment-report, /admin/payment-report/custom,
     and /admin/payment-report/pdf — previously wired up server-side
     but never surfaced in the admin panel.
  ---------------------------------------------------------- */
  function renderPeriodReportTable(rows) {
    const wrap = $("#periodReportWrap");
    if (!rows || rows.length === 0) {
      wrap.innerHTML = '<p class="empty-mini">No payouts recorded for this window.</p>';
      return;
    }
    const total = rows.reduce((sum, r) => sum + Number(r.total_amount), 0);
    wrap.innerHTML = `
      <table class="report-table">
        <thead><tr><th>Payment method</th><th>Payments</th><th>Total paid</th></tr></thead>
        <tbody>
          ${rows
            .slice()
            .sort((a, b) => Number(b.total_amount) - Number(a.total_amount))
            .map(
              (r) =>
                `<tr><td>${escapeHtml(r.payment_method_name)}</td><td>${r.payment_count}</td><td>${fmtMoney(r.total_amount)}</td></tr>`
            )
            .join("")}
        </tbody>
        <tfoot>
          <tr><td style="font-weight:600;">Total</td><td></td><td style="font-family:var(--font-mono);font-weight:700;">${fmtMoney(total)}</td></tr>
        </tfoot>
      </table>
    `;
  }

  function togglePeriodReportFields() {
    const isCustom = $("#periodReportType").value === "custom";
    $("#periodReportDateField").hidden = isCustom;
    $("#periodReportStartField").hidden = !isCustom;
    $("#periodReportEndField").hidden = !isCustom;
    $("#downloadPeriodReportPdf").disabled = isCustom;
    $("#downloadPeriodReportPdf").title = isCustom
      ? "PDF export is only available for daily, weekly, or monthly periods"
      : "";
  }

  $("#periodReportType").addEventListener("change", togglePeriodReportFields);
  togglePeriodReportFields();

  function periodReportQuery() {
    const type = $("#periodReportType").value;
    if (type === "custom") {
      const start = $("#periodReportStart").value;
      const end = $("#periodReportEnd").value;
      if (!start || !end) throw new Error("Choose a start and end date");
      return { custom: true, qs: `start_date=${start}&end_date=${end}` };
    }
    const date = $("#periodReportDate").value;
    const qs = `period=${type}` + (date ? `&report_date=${date}` : "");
    return { custom: false, qs };
  }

  $("#periodReportForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const wrap = $("#periodReportWrap");
    wrap.innerHTML = '<p class="empty-mini">Loading&hellip;</p>';
    try {
      const { custom, qs } = periodReportQuery();
      const path = custom ? `/admin/payment-report/custom?${qs}` : `/admin/payment-report?${qs}`;
      const rows = await api(path);
      renderPeriodReportTable(rows);
    } catch (err) {
      wrap.innerHTML = `<p class="empty-mini">Could not load report: ${escapeHtml(err.message || "unknown error")}</p>`;
    }
  });

  $("#downloadPeriodReportPdf").addEventListener("click", () => {
    try {
      const { custom, qs } = periodReportQuery();
      if (custom) return; // button is disabled in this state, but guard anyway
      window.open(`/admin/payment-report/pdf?${qs}`, "_blank");
    } catch (err) {
      toast(err.message || "Could not download PDF", "error");
    }
  });

  /* ----------------------------------------------------------
     Rendering — status queues
  ---------------------------------------------------------- */
  function statusBadge(status) {
    const cls = "badge-" + status.toLowerCase();
    return `<span class="badge ${cls}">${status}</span>`;
  }

  function categoryCell(e) {
    return `${e.category ? escapeHtml(e.category.category_name) : "—"}${e.subcategory ? ` <span class="muted">· ${escapeHtml(e.subcategory.subcategory_name)}</span>` : ""}`;
  }

  function expenseCell(e) {
    return `
      <div class="cell-title">${escapeHtml(e.title)}</div>
      <span class="cell-expense-num">${escapeHtml(e.expense_number)}</span>
    `;
  }

  function renderPendingTable() {
    const body = $("#pendingTableBody");
    const empty = $("#pendingEmpty");
    body.innerHTML = "";

    if (state.pending.length === 0) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;

    state.pending.forEach((e) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${expenseCell(e)}</td>
        <td class="cell-meta">Employee #${e.created_by}</td>
        <td>${fmtDate(e.expense_date)}</td>
        <td>${categoryCell(e)}</td>
        <td class="cell-amount">${fmtMoney(e.amount)}</td>
        <td class="col-actions">
          <div class="row-actions">
            <button class="btn btn-ghost btn-sm" data-action="receipt" data-id="${e.id}">Receipt</button>
            <button class="btn btn-primary btn-sm" data-action="approve" data-id="${e.id}">Approve</button>
            <button class="btn btn-danger btn-sm" data-action="reject" data-id="${e.id}">Reject</button>
          </div>
        </td>
      `;
      body.appendChild(tr);
    });
  }

  function renderApprovedTable() {
    const body = $("#approvedTableBody");
    const empty = $("#approvedEmpty");
    body.innerHTML = "";

    if (state.approved.length === 0) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;

    state.approved.forEach((e) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${expenseCell(e)}</td>
        <td class="cell-meta">Employee #${e.created_by}</td>
        <td class="cell-meta">${fmtDateTime(e.approved_at)}</td>
        <td>${categoryCell(e)}</td>
        <td class="cell-amount">${fmtMoney(e.amount)}</td>
        <td class="col-actions">
          <div class="row-actions">
            <button class="btn btn-ghost btn-sm" data-action="receipt" data-id="${e.id}">Receipt</button>
            <button class="btn btn-primary btn-sm" data-action="paid" data-id="${e.id}">Mark paid</button>
          </div>
        </td>
      `;
      body.appendChild(tr);
    });
  }

  function renderPaidTable() {
    const body = $("#paidTableBody");
    const empty = $("#paidEmpty");
    body.innerHTML = "";

    if (state.paid.length === 0) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;

    state.paid.forEach((e) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${expenseCell(e)}</td>
        <td class="cell-meta">Employee #${e.created_by}</td>
        <td class="cell-meta">${fmtDateTime(e.paid_at)}</td>
        <td>${categoryCell(e)}</td>
        <td class="cell-amount">${fmtMoney(e.amount)}</td>
        <td class="col-actions">
          <div class="row-actions">
            <button class="btn btn-ghost btn-sm" data-action="receipt" data-id="${e.id}">Receipt</button>
            <button class="btn btn-ghost btn-sm" data-action="edit-payment" data-id="${e.id}">Cheque / payment details</button>
          </div>
        </td>
      `;
      body.appendChild(tr);
    });
  }

  function renderRejectedTable() {
    const body = $("#rejectedTableBody");
    const empty = $("#rejectedEmpty");
    body.innerHTML = "";

    if (state.rejected.length === 0) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;

    state.rejected.forEach((e) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${expenseCell(e)}</td>
        <td class="cell-meta">Employee #${e.created_by}</td>
        <td>
          <div class="cell-meta">${fmtDateTime(e.approved_at)}</div>
          ${e.remarks ? `<div class="cell-reason">${escapeHtml(e.remarks)}</div>` : ""}
        </td>
        <td>${categoryCell(e)}</td>
        <td class="cell-amount">${fmtMoney(e.amount)}</td>
        <td class="col-actions">
          <div class="row-actions">
            <button class="btn btn-ghost btn-sm" data-action="receipt" data-id="${e.id}">Receipt</button>
          </div>
        </td>
      `;
      body.appendChild(tr);
    });
  }

  /* ----------------------------------------------------------
     Row actions (event delegation across all queue tables)
  ---------------------------------------------------------- */
  function findExpenseById(id) {
    return (
      state.pending.find((e) => String(e.id) === String(id)) ||
      state.approved.find((e) => String(e.id) === String(id)) ||
      state.rejected.find((e) => String(e.id) === String(id)) ||
      state.paid.find((e) => String(e.id) === String(id))
    );
  }

  ["#pendingTableBody", "#approvedTableBody", "#rejectedTableBody", "#paidTableBody"].forEach((sel) => {
    $(sel).addEventListener("click", async (e) => {
      const btn = e.target.closest("button[data-action]");
      if (!btn) return;
      const id = btn.dataset.id;
      const action = btn.dataset.action;

      try {
        if (action === "approve") {
          await approveExpense(id);
        } else if (action === "reject") {
          openRejectModal(id);
        } else if (action === "paid") {
          openPaidModal(id);
        } else if (action === "edit-payment") {
          openEditPaymentModal(id);
        } else if (action === "receipt") {
          showReceipt(id);
        }
      } catch (err) {
        toast(err.message || "Something went wrong", "error");
      }
    });
  });

  async function approveExpense(id) {
    await api(`/admin/expenses/${id}/approve`, { method: "PUT", json: { approved_by: adminId() } });
    toast("Expense approved", "success");
    await Promise.all([loadPending(), loadApproved(), loadDashboard()]);
  }

  /* ----------------------------------------------------------
     Mark as paid modal
  ---------------------------------------------------------- */
  let paidTargetId = null;

  function renderPaymentMethodOptions() {
    const select = $("#paidMethodSelect");
    const current = select.value;
    select.innerHTML = '<option value="">Select a payment method&hellip;</option>' +
      state.paymentMethods
        .map((m) => `<option value="${m.id}" data-name="${escapeHtml(m.payment_method_name.toLowerCase())}">${escapeHtml(m.payment_method_name)}</option>`)
        .join("");
    select.value = current;
  }

  function fieldsForMethodName(name) {
    return PAYMENT_METHOD_FIELD_GROUPS[(name || "").toLowerCase()] || [];
  }

  const PAID_FIELD_IDS = {
    cheque_number: "#fieldChequeNumber",
    bank_name: "#fieldBankName",
    account_last_four: "#fieldAccountLastFour",
    transaction_reference: "#fieldTransactionReference",
  };

  function updatePaidFieldVisibility() {
    const select = $("#paidMethodSelect");
    const opt = select.options[select.selectedIndex];
    const methodName = opt ? opt.dataset.name : "";
    const needed = fieldsForMethodName(methodName);

    Object.entries(PAID_FIELD_IDS).forEach(([field, sel]) => {
      const wrap = $(sel);
      const input = wrap.querySelector("input");
      const isNeeded = needed.includes(field);
      wrap.hidden = !isNeeded;
      input.required = isNeeded;
      if (!isNeeded) input.value = "";
    });
  }

  $("#paidMethodSelect").addEventListener("change", updatePaidFieldVisibility);

  function openPaidModal(id) {
    paidTargetId = id;
    $("#paidForm").reset();
    updatePaidFieldVisibility();
    openModal("#paidBackdrop");
  }

  $("#paidForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!paidTargetId) return;
    const formData = new FormData(e.target);

    const payload = {
      paid_by: adminId(),
      payment_method_id: Number(formData.get("payment_method_id")),
      cheque_number: formData.get("cheque_number") || null,
      bank_name: formData.get("bank_name") || null,
      account_last_four: formData.get("account_last_four") || null,
      transaction_reference: formData.get("transaction_reference") || null,
      remarks: formData.get("remarks") || null,
    };
    const paymentDate = formData.get("payment_date");
    if (paymentDate) payload.payment_date = new Date(paymentDate).toISOString();

    try {
      await api(`/admin/expenses/${paidTargetId}/paid`, { method: "PUT", json: payload });
      toast("Marked as paid", "success");
      closeModal("#paidBackdrop");
      await Promise.all([loadApproved(), loadPaid(), loadDashboard(), loadPaymentMethodReport()]);
    } catch (err) {
      toast(err.message || "Could not mark expense as paid", "error");
    }
  });

  $("#cancelPaid").addEventListener("click", () => closeModal("#paidBackdrop"));
  $("#closePaidModal").addEventListener("click", () => closeModal("#paidBackdrop"));

  /* ----------------------------------------------------------
     Edit payment details (correct/add cheque number etc.)
  ---------------------------------------------------------- */
  let editPaymentTargetId = null;

  function openEditPaymentModal(id) {
    editPaymentTargetId = id;
    const expense = findExpenseById(id);
    const form = $("#editPaymentForm");
    form.reset();
    if (expense) {
      form.elements.cheque_number.value = expense.cheque_number || "";
      form.elements.bank_name.value = expense.bank_name || "";
      form.elements.account_last_four.value = expense.account_last_four || "";
      form.elements.transaction_reference.value = expense.transaction_reference || "";
    }
    openModal("#editPaymentBackdrop");
  }

  $("#editPaymentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!editPaymentTargetId) return;
    const formData = new FormData(e.target);

    const payload = {};
    ["cheque_number", "bank_name", "account_last_four", "transaction_reference"].forEach((field) => {
      const value = formData.get(field);
      if (value) payload[field] = value;
    });
    const paymentDate = formData.get("payment_date");
    if (paymentDate) payload.payment_date = new Date(paymentDate).toISOString();

    try {
      await api(`/admin/expenses/${editPaymentTargetId}/payment-details`, { method: "PUT", json: payload });
      toast("Payment details saved", "success");
      closeModal("#editPaymentBackdrop");
      await Promise.all([loadPaid(), loadPaymentMethodReport()]);
    } catch (err) {
      toast(err.message || "Could not save payment details", "error");
    }
  });

  $("#cancelEditPayment").addEventListener("click", () => closeModal("#editPaymentBackdrop"));
  $("#closeEditPaymentModal").addEventListener("click", () => closeModal("#editPaymentBackdrop"));

  function showReceipt(id) {
    const expense = findExpenseById(id);
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
     Reject modal
  ---------------------------------------------------------- */
  let rejectTargetId = null;

  function openRejectModal(id) {
    rejectTargetId = id;
    $("#rejectForm").reset();
    openModal("#rejectBackdrop");
  }

  $("#rejectForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!rejectTargetId) return;
    const formData = new FormData(e.target);

    try {
      await api(`/admin/expenses/${rejectTargetId}/reject`, {
        method: "PUT",
        json: { approved_by: adminId(), remarks: formData.get("remarks") || "" },
      });
      toast("Expense rejected", "success");
      closeModal("#rejectBackdrop");
      await Promise.all([loadPending(), loadRejected(), loadDashboard()]);
    } catch (err) {
      toast(err.message || "Could not reject expense", "error");
    }
  });

  $("#cancelReject").addEventListener("click", () => closeModal("#rejectBackdrop"));
  $("#closeRejectModal").addEventListener("click", () => closeModal("#rejectBackdrop"));
  $("#closeReceiptModal").addEventListener("click", () => closeModal("#receiptBackdrop"));

  function openModal(sel) {
    $(sel).classList.add("is-open");
  }
  function closeModal(sel) {
    $(sel).classList.remove("is-open");
  }

  $$(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) backdrop.classList.remove("is-open");
    });
  });

  /* clicking a dashboard stat card jumps to that queue */
  $("#statStrip").addEventListener("click", (e) => {
    const card = e.target.closest(".stat-card[data-view]");
    if (card) setView(card.dataset.view);
  });

  /* ----------------------------------------------------------
     Categories & subcategories
  ---------------------------------------------------------- */
  function renderCategoryParentOptions() {
    const select = $("#subcategoryParentSelect");
    const current = select.value;
    select.innerHTML = '<option value="">Select a category&hellip;</option>' +
      state.categories
        .slice()
        .sort((a, b) => a.category_name.localeCompare(b.category_name))
        .map((c) => `<option value="${c.id}">${escapeHtml(c.category_name)}</option>`)
        .join("");
    select.value = current;
  }

  function renderCategoryList() {
    const wrap = $("#categoryListWrap");
    if (state.categories.length === 0) {
      wrap.innerHTML = '<p class="empty-mini">No categories yet — add one above.</p>';
      return;
    }

    wrap.innerHTML = state.categories
      .slice()
      .sort((a, b) => a.category_name.localeCompare(b.category_name))
      .map((c) => {
        const subs = state.subcategories.filter((s) => s.category_id === c.id);
        return `
          <div class="detail-row" style="align-items:flex-start;">
            <span class="detail-label" style="font-weight:600; color:var(--ink);">${escapeHtml(c.category_name)}</span>
            <span class="detail-value" style="text-align:right; font-family:inherit;">
              ${subs.length ? subs.map((s) => escapeHtml(s.subcategory_name)).join(", ") : '<span class="muted">No subcategories</span>'}
            </span>
          </div>
        `;
      })
      .join("");
  }

  $("#categoryForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const name = (formData.get("category_name") || "").trim();
    if (!name) return;

    try {
      await api("/admin/categories", { method: "POST", json: { category_name: name } });
      toast("Category added", "success");
      e.target.reset();
      await loadCategories();
    } catch (err) {
      toast(err.message || "Could not add category", "error");
    }
  });

  $("#subcategoryForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const categoryId = Number(formData.get("category_id"));
    const name = (formData.get("subcategory_name") || "").trim();
    if (!categoryId || !name) return;

    try {
      await api("/admin/subcategories", {
        method: "POST",
        json: { category_id: categoryId, subcategory_name: name },
      });
      toast("Subcategory added", "success");
      e.target.reset();
      await loadCategories();
    } catch (err) {
      toast(err.message || "Could not add subcategory", "error");
    }
  });

  /* ----------------------------------------------------------
     Payment methods (admin-managed reference data)
  ---------------------------------------------------------- */
  function renderPaymentMethodList() {
    const wrap = $("#paymentMethodListWrap");
    if (state.paymentMethods.length === 0) {
      wrap.innerHTML = '<p class="empty-mini">No payment methods yet — add one, or use "Add common methods".</p>';
      return;
    }
    wrap.innerHTML = state.paymentMethods
      .slice()
      .sort((a, b) => a.payment_method_name.localeCompare(b.payment_method_name))
      .map((m) => `<div class="detail-row"><span class="detail-label">${escapeHtml(m.payment_method_name)}</span></div>`)
      .join("");
  }

  async function createPaymentMethod(name) {
    try {
      await api("/admin/payment-methods", { method: "POST", json: { payment_method_name: name } });
      return true;
    } catch (err) {
      // Likely "already exists" — safe to ignore during bulk add.
      return false;
    }
  }

  $("#paymentMethodForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const name = (formData.get("payment_method_name") || "").trim();
    if (!name) return;

    try {
      await api("/admin/payment-methods", { method: "POST", json: { payment_method_name: name } });
      toast("Payment method added", "success");
      e.target.reset();
      await loadPaymentMethods();
    } catch (err) {
      toast(err.message || "Could not add payment method", "error");
    }
  });

  const COMMON_PAYMENT_METHODS = [
    "Cash", "Cheque", "Debit Card", "Credit Card", "Corporate Card",
    "UPI", "Google Pay", "PhonePe", "Amazon Pay", "Paytm Wallet",
    "Bank Account", "Bank Transfer", "Net Banking", "NEFT", "RTGS", "IMPS",
  ];

  $("#quickAddPaymentMethods").addEventListener("click", async () => {
    const existing = new Set(state.paymentMethods.map((m) => m.payment_method_name.toLowerCase()));
    const toAdd = COMMON_PAYMENT_METHODS.filter((n) => !existing.has(n.toLowerCase()));

    if (toAdd.length === 0) {
      toast("All common methods are already added");
      return;
    }

    await Promise.all(toAdd.map((n) => createPaymentMethod(n)));
    toast(`Added ${toAdd.length} payment method${toAdd.length === 1 ? "" : "s"}`, "success");
    await loadPaymentMethods();
  });

  /* ----------------------------------------------------------
     Init
  ---------------------------------------------------------- */
  const todayStr = new Date().toISOString().slice(0, 10);
  if ($("#periodReportDate")) $("#periodReportDate").value = todayStr;
  if ($("#periodReportStart")) $("#periodReportStart").value = todayStr;
  if ($("#periodReportEnd")) $("#periodReportEnd").value = todayStr;

  refreshAll().catch((err) => {
    console.error(err);
    toast("Could not reach the API. Is the backend running?", "error");
  });
})();
