(() => {
  "use strict";

  const API = "";

  const $ = (sel, root = document) => root.querySelector(sel);

  const adminId = () => Number(($("#adminIdInput") || {}).value || 1);

  const state = {
    ownerType: "",
    ownerId: null,
    wallet: null,
    transactions: [],
  };

  const fmtMoney = (value) => {
    const n = Number(value || 0);
    return "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 0 });
  };

  const fmtDateTime = (value) => {
    if (!value) return "—";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
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
    const opts = { ...options, credentials: "same-origin" };
    if (opts.json !== undefined) {
      opts.headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
      opts.body = JSON.stringify(opts.json);
      delete opts.json;
    }
    const res = await fetch(API + path, opts);
    if (res.status === 401 && window.LedgerSession) {
      window.LedgerSession.goToLogin();
      return new Promise(() => {});
    }
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || JSON.stringify(body);
      } catch (_) { /* ignore */ }
      const err = new Error(typeof detail === "string" ? detail : "Request failed");
      err.status = res.status;
      throw err;
    }
    if (res.status === 204) return null;
    return res.json();
  }

  function ownerLabel() {
    if (!state.ownerType || !state.ownerId) return "No wallet loaded yet";
    const typeLabel = state.ownerType === "SUB_VENDOR" ? "Sub-vendor" : "Employee";
    return `${typeLabel} #${state.ownerId}`;
  }

  function resetWalletDisplay(message) {
    state.wallet = null;
    state.transactions = [];
    $("#walletStatusLabel").textContent = message || ownerLabel();
    $("#walletBalance").textContent = fmtMoney(0);
    $("#walletCurrency").textContent = "—";
    $("#walletActiveState").textContent = "—";
    $("#walletCreatedAt").textContent = "—";
    renderTransactions();
  }

  function renderWallet() {
    if (!state.wallet) {
      resetWalletDisplay();
      return;
    }
    $("#walletStatusLabel").textContent = ownerLabel();
    $("#walletBalance").textContent = fmtMoney(state.wallet.balance);
    $("#walletCurrency").textContent = state.wallet.currency || "—";
    $("#walletActiveState").textContent = state.wallet.is_active ? "Active" : "Inactive";
    $("#walletCreatedAt").textContent = `Created ${fmtDateTime(state.wallet.created_at)}`;
    renderTransactions();
  }

  function renderTransactions() {
    const body = $("#walletTransactionsBody");
    const empty = $("#walletTransactionsEmpty");
    if (!state.transactions.length) {
      body.innerHTML = "";
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    body.innerHTML = state.transactions
      .map((t) => {
        const typeClass = t.transaction_type === "CREDIT" ? "badge-approved" : "badge-rejected";
        const reference = t.reference_type
          ? `${escapeHtml(t.reference_type)}${t.reference_id ? " #" + escapeHtml(t.reference_id) : ""}`
          : "—";
        return `
          <tr>
            <td>${fmtDateTime(t.created_at)}</td>
            <td><span class="badge ${typeClass}">${escapeHtml(t.transaction_type)}</span></td>
            <td>${fmtMoney(t.amount)}</td>
            <td>${fmtMoney(t.balance_after)}</td>
            <td>${reference}</td>
            <td>${escapeHtml(t.description || "—")}</td>
            <td>${t.performed_by != null ? escapeHtml(t.performed_by) : "—"}</td>
          </tr>
        `;
      })
      .join("");
  }

  async function loadWallet(ownerType, ownerId) {
    state.ownerType = ownerType;
    state.ownerId = ownerId;
    try {
      const data = await api(`/wallet/${ownerType}/${ownerId}`);
      state.wallet = data.wallet;
      state.transactions = data.transactions || [];
      renderWallet();
    } catch (err) {
      if (err.status === 404) {
        resetWalletDisplay(`No wallet found for ${ownerLabel()}`);
        toast("No wallet found for that owner", "error");
      } else {
        resetWalletDisplay();
        toast(err.message || "Could not load wallet", "error");
      }
      throw err;
    }
  }

  const lookupForm = $("#walletLookupForm");
  if (lookupForm) {
    lookupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const ownerType = formData.get("owner_type");
      const ownerId = Number(formData.get("owner_id"));
      if (!ownerType || !ownerId) return;
      try {
        await loadWallet(ownerType, ownerId);
        toast("Wallet loaded", "success");
      } catch (_) {
        // already toasted in loadWallet
      }
    });
  }

  const transactionForm = $("#walletTransactionForm");
  if (transactionForm) {
    transactionForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (!state.ownerType || !state.ownerId) {
        toast("Select an owner type and ID above first", "error");
        return;
      }

      const formData = new FormData(e.target);
      const amount = Number(formData.get("amount"));
      if (!amount || amount <= 0) {
        toast("Enter an amount greater than zero", "error");
        return;
      }

      const payload = {
        owner_type: state.ownerType,
        owner_id: state.ownerId,
        transaction_type: formData.get("transaction_type"),
        amount,
        performed_by: adminId(),
        reference_type: formData.get("reference_type") || null,
        reference_id: formData.get("reference_id") ? Number(formData.get("reference_id")) : null,
        description: formData.get("description") || null,
      };

      const submitBtn = transactionForm.querySelector("button[type=submit]");
      submitBtn.disabled = true;

      try {
        await api("/admin/wallet/transactions", { method: "POST", json: payload });
        toast("Wallet transaction recorded", "success");
        e.target.reset();
        await loadWallet(state.ownerType, state.ownerId);
      } catch (err) {
        toast(err.message || "Could not record transaction", "error");
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  resetWalletDisplay();
})();
