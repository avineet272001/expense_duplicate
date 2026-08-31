(() => {
  "use strict";

  /* ----------------------------------------------------------
     Config
     API is same-origin ("") because this frontend is served by
     the FastAPI app itself at the root ("/"). If you ever host
     this frontend on a different origin, set API to the full
     backend URL AND make sure the backend's CORS config lists
     that exact origin (not "*") since auth uses httpOnly cookies.
  ---------------------------------------------------------- */
  const API = "";
  const SESSION_KEY = "ledger_employee";

  const $ = (sel, root = document) => root.querySelector(sel);

  async function api(path, options = {}) {
    const opts = { ...options, credentials: "same-origin" };
    if (opts.json !== undefined) {
      opts.headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
      opts.body = JSON.stringify(opts.json);
      delete opts.json;
    }
    const res = await fetch(API + path, opts);
    let body = null;
    try { body = await res.json(); } catch (_) { /* no body */ }

    if (!res.ok) {
      const detail = (body && (body.detail || body.message)) || res.statusText || "Request failed";
      const err = new Error(typeof detail === "string" ? detail : "Request failed");
      err.status = res.status;
      throw err;
    }
    return body;
  }

  function saveSession(data) {
    localStorage.setItem(SESSION_KEY, JSON.stringify({
      employee_id: data.employee_id,
      sub_vendor_id: data.sub_vendor_id,
      name: data.name,
      email: data.email,
    }));
  }

  function showAlert(el, message, type = "error") {
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
    el.className = "auth-alert auth-alert--" + type;
  }

  function hideAlert(el) {
    if (!el) return;
    el.hidden = true;
  }

  function setLoading(button, loading, labelWhenIdle) {
    if (!button) return;
    button.disabled = loading;
    button.innerHTML = loading
      ? '<span class="spinner"></span> Please wait&hellip;'
      : labelWhenIdle;
  }

  /* ----------------------------------------------------------
     Password show/hide toggle
  ---------------------------------------------------------- */
  document.querySelectorAll(".auth-toggle-pw").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.target);
      if (!input) return;
      const isPw = input.type === "password";
      input.type = isPw ? "text" : "password";
      btn.textContent = isPw ? "Hide" : "Show";
    });
  });

  /* ----------------------------------------------------------
     LOGIN PAGE
  ---------------------------------------------------------- */
  const loginForm = $("#loginForm");
  if (loginForm) {
    const alertBox = $("#loginAlert");
    const submitBtn = $("#loginSubmit");

    const params = new URLSearchParams(window.location.search);
    if (params.get("loggedout") === "1") {
      showAlert(alertBox, "You've been signed out.", "success");
    }
    if (params.get("deactivated") === "1") {
      showAlert(alertBox, "Your account has been deactivated by your sub-vendor. Contact them to be reactivated.");
    }

    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideAlert(alertBox);

      const formData = new FormData(loginForm);
      const email = (formData.get("email") || "").trim();
      const password = formData.get("password") || "";

      if (!email || !password) {
        showAlert(alertBox, "Enter your email and password.");
        return;
      }

      setLoading(submitBtn, true);
      try {
        // Backend schema (EmployeeLogin) expects "email", not "email_id".
        const data = await api("/expenses/login", { method: "POST", json: { email, password } });
        saveSession(data);
        window.location.href = "index.html";
      } catch (err) {
        if (err.status === 403) {
          showAlert(alertBox, err.message || "Your account has been deactivated.");
        } else {
          showAlert(alertBox, err.message || "Invalid email or password.");
        }
      } finally {
        setLoading(submitBtn, false, "Sign in");
      }
    });
  }
})();
