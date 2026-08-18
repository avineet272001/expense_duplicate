(() => {
  "use strict";

  const API = "";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const adminId = () => Number(($("#adminIdInput") || {}).value || 1);

  const fmtDateTime = (value) => {
    if (!value) return "—";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
  };

  function escapeHtml(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function toast(message, type = "default") {
    const stack = $("#toastStack");
    if (!stack) return;
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

  function badgeFor(status) {
    const s = (status || "").toUpperCase();
    const cls = s === "APPROVED" ? "badge-approved" : s === "REJECTED" ? "badge-rejected" : "badge-pending";
    return `<span class="badge ${cls}">${escapeHtml(s || "PENDING")}</span>`;
  }

  /* ----------------------------------------------------------
     Category requests
  ---------------------------------------------------------- */
  let categoryRequestStatus = "PENDING";
  let subcategoryRequestStatus = "PENDING";
  let categoriesById = {};

  async function loadCategoryRequests() {
    const qs = categoryRequestStatus ? `?status=${encodeURIComponent(categoryRequestStatus)}` : "";
    const rows = await api(`/admin/category-requests${qs}`);
    renderCategoryRequests(rows);
    return rows;
  }

  function renderCategoryRequests(rows) {
    const body = $("#categoryRequestsTableBody");
    const empty = $("#categoryRequestsEmpty");
    if (!body) return;
    if (!rows || rows.length === 0) {
      body.innerHTML = "";
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;

    body.innerHTML = rows.map((r) => `
      <tr>
        <td class="cell-title">${escapeHtml(r.category_name)}</td>
        <td>User ${r.requested_by}</td>
        <td class="cell-reason">${escapeHtml(r.remarks || "—")}</td>
        <td>${badgeFor(r.status)}</td>
        <td>${fmtDateTime(r.created_at)}</td>
        <td class="col-actions">
          ${r.status === "PENDING" ? `
            <div class="row-actions">
              <button class="btn btn-sm btn-primary" data-approve-cat="${r.id}">Approve</button>
              <button class="btn btn-sm btn-danger" data-reject-cat="${r.id}">Reject</button>
            </div>
          ` : (r.rejection_reason ? `<span class="cell-reason muted">${escapeHtml(r.rejection_reason)}</span>` : "—")}
        </td>
      </tr>
    `).join("");
  }

  async function loadSubcategoryRequests() {
    const qs = subcategoryRequestStatus ? `?status=${encodeURIComponent(subcategoryRequestStatus)}` : "";
    const rows = await api(`/admin/subcategory-requests${qs}`);
    renderSubcategoryRequests(rows);
    return rows;
  }

  function renderSubcategoryRequests(rows) {
    const body = $("#subcategoryRequestsTableBody");
    const empty = $("#subcategoryRequestsEmpty");
    if (!body) return;
    if (!rows || rows.length === 0) {
      body.innerHTML = "";
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;

    body.innerHTML = rows.map((r) => `
      <tr>
        <td class="cell-title">${escapeHtml(r.subcategory_name)}</td>
        <td>${escapeHtml((categoriesById[r.category_id] || {}).category_name || ("#" + r.category_id))}</td>
        <td>User ${r.requested_by}</td>
        <td class="cell-reason">${escapeHtml(r.remarks || "—")}</td>
        <td>${badgeFor(r.status)}</td>
        <td>${fmtDateTime(r.created_at)}</td>
        <td class="col-actions">
          ${r.status === "PENDING" ? `
            <div class="row-actions">
              <button class="btn btn-sm btn-primary" data-approve-subcat="${r.id}">Approve</button>
              <button class="btn btn-sm btn-danger" data-reject-subcat="${r.id}">Reject</button>
            </div>
          ` : (r.rejection_reason ? `<span class="cell-reason muted">${escapeHtml(r.rejection_reason)}</span>` : "—")}
        </td>
      </tr>
    `).join("");
  }

  async function refreshVendorRequestCounts() {
    try {
      const [pendingCats, pendingSubs] = await Promise.all([
        api("/admin/category-requests?status=PENDING"),
        api("/admin/subcategory-requests?status=PENDING"),
      ]);
      const total = (pendingCats || []).length + (pendingSubs || []).length;
      const badge = $("#navVendorRequestCount");
      if (badge) badge.textContent = total;
    } catch (_) { /* ignore */ }
  }

  async function refreshVendorRequestsView() {
    try {
      const cats = await api("/expenses/categories").catch(() => api("/admin/categories").catch(() => []));
      categoriesById = {};
      (cats || []).forEach((c) => { categoriesById[c.id] = c; });
    } catch (_) { /* ignore, fall back to raw ids */ }

    await Promise.all([loadCategoryRequests(), loadSubcategoryRequests()]);
    await refreshVendorRequestCounts();
  }

  $$("#categoryRequestTabs .tab-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$("#categoryRequestTabs .tab-pill").forEach((b) => b.classList.toggle("is-active", b === btn));
      categoryRequestStatus = btn.dataset.status;
      loadCategoryRequests().catch((err) => toast(err.message, "error"));
    });
  });

  $$("#subcategoryRequestTabs .tab-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$("#subcategoryRequestTabs .tab-pill").forEach((b) => b.classList.toggle("is-active", b === btn));
      subcategoryRequestStatus = btn.dataset.status;
      loadSubcategoryRequests().catch((err) => toast(err.message, "error"));
    });
  });

  /* Approve / reject wiring (delegated) */
  let rejectRequestTarget = null; // { kind: 'category'|'subcategory', id }

  document.addEventListener("click", async (e) => {
    const approveCat = e.target.closest("[data-approve-cat]");
    const rejectCat = e.target.closest("[data-reject-cat]");
    const approveSubcat = e.target.closest("[data-approve-subcat]");
    const rejectSubcat = e.target.closest("[data-reject-subcat]");

    if (approveCat) {
      try {
        await api(`/admin/category-requests/${approveCat.dataset.approveCat}/approve`, {
          method: "PUT", json: { approved_by: adminId() },
        });
        toast("Category request approved", "success");
        await refreshVendorRequestsView();
      } catch (err) { toast(err.message || "Could not approve request", "error"); }
    }

    if (approveSubcat) {
      try {
        await api(`/admin/subcategory-requests/${approveSubcat.dataset.approveSubcat}/approve`, {
          method: "PUT", json: { approved_by: adminId() },
        });
        toast("Subcategory request approved", "success");
        await refreshVendorRequestsView();
      } catch (err) { toast(err.message || "Could not approve request", "error"); }
    }

    if (rejectCat) {
      rejectRequestTarget = { kind: "category", id: rejectCat.dataset.rejectCat };
      $("#rejectRequestBackdrop").classList.add("is-open");
    }

    if (rejectSubcat) {
      rejectRequestTarget = { kind: "subcategory", id: rejectSubcat.dataset.rejectSubcat };
      $("#rejectRequestBackdrop").classList.add("is-open");
    }
  });

  function closeRejectRequestModal() {
    $("#rejectRequestBackdrop").classList.remove("is-open");
    $("#rejectRequestForm").reset();
    rejectRequestTarget = null;
  }
  $("#closeRejectRequestModal").addEventListener("click", closeRejectRequestModal);
  $("#cancelRejectRequest").addEventListener("click", closeRejectRequestModal);

  $("#rejectRequestForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!rejectRequestTarget) return;
    const formData = new FormData(e.target);
    const reason = (formData.get("rejection_reason") || "").trim();
    if (!reason) return;

    const path = rejectRequestTarget.kind === "category"
      ? `/admin/category-requests/${rejectRequestTarget.id}/reject`
      : `/admin/subcategory-requests/${rejectRequestTarget.id}/reject`;

    try {
      await api(path, { method: "PUT", json: { rejected_by: adminId(), rejection_reason: reason } });
      toast("Request rejected", "success");
      closeRejectRequestModal();
      await refreshVendorRequestsView();
    } catch (err) {
      toast(err.message || "Could not reject request", "error");
    }
  });

  /* ----------------------------------------------------------
     Activity log
  ---------------------------------------------------------- */
  async function loadActivityLog() {
    const userId = ($("#activityUserIdFilter").value || "").trim();
    const moduleVal = $("#activityModuleFilter").value;
    const actionVal = ($("#activityActionFilter").value || "").trim();

    const params = new URLSearchParams();
    if (userId) params.set("user_id", userId);
    if (moduleVal) params.set("module", moduleVal);
    if (actionVal) params.set("action", actionVal);

    const qs = params.toString() ? `?${params.toString()}` : "";
    const rows = await api(`/admin/sub-vendor-activities${qs}`);
    renderActivityLog(rows);
  }

  function renderActivityLog(rows) {
    const body = $("#activityLogTableBody");
    const empty = $("#activityLogEmpty");
    if (!rows || rows.length === 0) {
      body.innerHTML = "";
      empty.hidden = false;
      return;
    }
    empty.hidden = true;

    body.innerHTML = rows
      .slice()
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      .map((r) => `
        <tr>
          <td>${fmtDateTime(r.created_at)}</td>
          <td>User ${r.user_id}</td>
          <td>${escapeHtml(r.module)}</td>
          <td>${escapeHtml(r.action)}</td>
          <td>${escapeHtml(r.description || "—")}</td>
          <td>${badgeFor(r.status === "SUCCESS" ? "APPROVED" : r.status === "FAILED" ? "REJECTED" : r.status)}</td>
        </tr>
      `).join("");
  }

  $("#activityLogFilterForm").addEventListener("submit", (e) => {
    e.preventDefault();
    loadActivityLog().catch((err) => toast(err.message || "Could not load activity", "error"));
  });

  $("#activityFilterReset").addEventListener("click", () => {
    $("#activityUserIdFilter").value = "";
    $("#activityModuleFilter").value = "";
    $("#activityActionFilter").value = "";
    loadActivityLog().catch((err) => toast(err.message || "Could not load activity", "error"));
  });

  /* Load lazily whenever these views are opened */
  $$("[data-view='vendor-requests']").forEach((el) => {
    el.addEventListener("click", () => refreshVendorRequestsView().catch((err) => toast(err.message, "error")));
  });
  $$("[data-view='activity-log']").forEach((el) => {
    el.addEventListener("click", () => loadActivityLog().catch((err) => toast(err.message, "error")));
  });

  /* Initial pending-count badge on load */
  refreshVendorRequestCounts();

  /* Expose a small hook other scripts (e.g. firebase-notify.js) can call
     to refresh the badge count after a push notification arrives. */
  window.__refreshVendorRequestCounts = refreshVendorRequestCounts;
})();
