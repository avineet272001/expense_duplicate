(() => {
  "use strict";

  const SESSION_KEY = "ledger_admin";

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

  // Expose a tiny global so app.js can redirect on 401 without
  // duplicating this logic, and so it always knows the real admin id.
  window.LedgerSession = { getSession, clearSession, goToLogin };

  /* ----------------------------------------------------------
     Optimistic guard: if we have no local session record, don't
     bother rendering the dashboard — bounce to login immediately.
     (The definitive check still happens server-side: if the
     admin_token cookie is missing/expired/revoked, the very first
     /admin/... API call app.js makes will 401 and LedgerSession
     will redirect then too.)
  ---------------------------------------------------------- */
  const session = getSession();
  if (!session || !session.admin_id) {
    goToLogin();
    return;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const nameEl = document.getElementById("userName");
    const emailEl = document.getElementById("userEmail");
    const avatarEl = document.getElementById("userAvatar");
    const adminIdInput = document.getElementById("adminIdInput");
    const logoutBtn = document.getElementById("logoutBtn");

    if (nameEl) nameEl.textContent = session.name || "Admin";
    if (emailEl) emailEl.textContent = session.email || "";
    if (avatarEl) avatarEl.textContent = (session.name || "A").trim().charAt(0).toUpperCase();
    if (adminIdInput) adminIdInput.value = session.admin_id;

    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        try {
          await fetch("/admin/logout", { method: "POST", credentials: "same-origin" });
        } catch (_) {
          // Even if the network call fails, still clear local state and leave.
        }
        window.LedgerSession.goToLogin("loggedout");
      });
    }
  });
})();
