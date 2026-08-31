(() => {
  "use strict";

  const API = "";

  const $ = (sel, root = document) => root.querySelector(sel);

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
    options.headers = { ...(window.Auth ? window.Auth.authHeader() : {}), ...(options.headers || {}) };
    const res = await fetch(API + path, options);
    if (res.status === 401) {
      window.Auth?.logout();
      const err = new Error("Session expired. Redirecting to sign in…");
      err.status = 401;
      throw err;
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

  function renderTransactions(transactions) {
    const body = $("#walletTransactionsBody");
    const empty = $("#walletTransactionsEmpty");
    if (!body || !empty) return;

    if (!transactions.length) {
      body.innerHTML = "";
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    body.innerHTML = transactions
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
          </tr>
        `;
      })
      .join("");
  }

  async function loadWallet() {
    const statusLabel = $("#walletStatusLabel");
    if (statusLabel) statusLabel.textContent = "Loading your wallet…";

    try {
      const data = await api("/sub-vendor/wallet");
      const wallet = data.wallet;
      $("#walletBalance").textContent = fmtMoney(wallet.balance);
      $("#walletCurrency").textContent = wallet.currency || "—";
      $("#walletActiveState").textContent = wallet.is_active ? "Active" : "Inactive";
      $("#walletCreatedAt").textContent = `Created ${fmtDateTime(wallet.created_at)}`;
      if (statusLabel) statusLabel.textContent = `Wallet #${wallet.id}`;
      renderTransactions(data.transactions || []);
    } catch (err) {
      if (statusLabel) {
        statusLabel.textContent = err.status === 404 ? "No wallet found for your account yet" : "Could not load your wallet";
      }
      $("#walletBalance").textContent = fmtMoney(0);
      $("#walletCurrency").textContent = "—";
      $("#walletActiveState").textContent = "—";
      $("#walletCreatedAt").textContent = "—";
      renderTransactions([]);
      if (err.status !== 404) {
        toast(err.message || "Could not load your wallet", "error");
      }
    }
  }

  document.querySelectorAll("[data-view='wallet']").forEach((el) => {
    el.addEventListener("click", () => loadWallet());
  });

  loadWallet();
})();
