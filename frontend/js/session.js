(() => {
  "use strict";

  const SESSION_KEY = "ledger_employee";

  function getSession() {
    try {
      return JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
    } catch (_) {
      return null;
    }
  }

  function clearSession() {
    localStorage.removeItem(SESSION_KEY);
  }

  function goToLogin(reason) {
    clearSession();
    const suffix = reason ? `?${reason}=1` : "";
    window.location.href = `login.html${suffix}`;
  }

  // Exposed so app.js / wallet.js can redirect on 401 and read the
  // logged-in employee's id without re-implementing session storage.
  window.LedgerSession = { getSession, clearSession, goToLogin };

  const session = getSession();
  if (!session || !session.employee_id) {
    goToLogin();
    return;
  }

  // Scripts are loaded at the end of <body>, so the DOM (including the
  // wallet lookup + expense modal fields) already exists — no need to
  // wait for DOMContentLoaded, and doing it synchronously here means
  // wallet.js's own initial-load code (which runs right after this file)
  // already sees the correct employee id.
  const label = document.getElementById("currentUserLabel");
  if (label) label.textContent = session.name || `#${session.employee_id}`;

  const createdByInput = document.getElementById("createdByInput");
  if (createdByInput) createdByInput.value = session.employee_id;

  const walletOwnerId = document.getElementById("walletOwnerId");
  if (walletOwnerId) walletOwnerId.value = session.employee_id;

  const sidebarFoot = document.querySelector(".sidebar-foot");
  if (sidebarFoot && !document.getElementById("logoutBtn")) {
    const btn = document.createElement("button");
    btn.id = "logoutBtn";
    btn.className = "btn btn-ghost";
    btn.style.width = "100%";
    btn.style.marginTop = "10px";
    btn.style.justifyContent = "center";
    btn.textContent = "Sign out";
    btn.addEventListener("click", async () => {
      try {
        await fetch("/expenses/logout", { method: "POST", credentials: "same-origin" });
      } catch (_) { /* still proceed to log out locally */ }
      window.LedgerSession.goToLogin("loggedout");
    });
    sidebarFoot.appendChild(btn);
  }
})();
