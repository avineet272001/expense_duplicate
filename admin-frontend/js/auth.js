(() => {
  "use strict";

  /* ----------------------------------------------------------
     Config
     API is same-origin ("") because this admin panel is served
     by the FastAPI app itself at /admin-ui/. If you ever host
     this frontend on a different origin, set API to the full
     backend URL (e.g. "https://api.example.com") AND make sure
     the backend's CORS config lists that exact origin (not "*")
     since auth uses httpOnly cookies + credentials.
  ---------------------------------------------------------- */
  const API = "";
  const SESSION_KEY = "ledger_admin";

  const $ = (sel, root = document) => root.querySelector(sel);

  /* ----------------------------------------------------------
     Small fetch helper — mirrors js/app.js's `api()` so both
     pages behave identically against the backend.
  ---------------------------------------------------------- */
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
      admin_id: data.admin_id,
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
     Password show/hide toggles (works on both pages)
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

    // If a previous page (e.g. register) wants to show a message.
    const params = new URLSearchParams(window.location.search);
    if (params.get("registered") === "1") {
      showAlert(alertBox, "Account created — sign in with your new password.", "success");
    }
    if (params.get("loggedout") === "1") {
      showAlert(alertBox, "You've been signed out.", "success");
    }

    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideAlert(alertBox);

      const formData = new FormData(loginForm);
      const email_id = (formData.get("email_id") || "").trim();
      const password = formData.get("password") || "";

      if (!email_id || !password) {
        showAlert(alertBox, "Enter your email and password.");
        return;
      }

      setLoading(submitBtn, true);
      try {
        const data = await api("/admin/login", { method: "POST", json: { email_id, password } });
        saveSession(data);
        window.location.href = "index.html";
      } catch (err) {
        showAlert(alertBox, err.message || "Invalid email or password.");
      } finally {
        setLoading(submitBtn, false, "Sign in");
      }
    });
  }

  /* ----------------------------------------------------------
     REGISTER PAGE
  ---------------------------------------------------------- */
  const registerForm = $("#registerForm");
  if (registerForm) {
    const alertBox = $("#registerAlert");
    const submitBtn = $("#registerSubmit");

    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideAlert(alertBox);

      const formData = new FormData(registerForm);
      const Name = (formData.get("Name") || "").trim();
      const email_id = (formData.get("email_id") || "").trim();
      const phone_number = (formData.get("phone_number") || "").trim();
      const password = formData.get("password") || "";
      const confirmPassword = formData.get("confirm_password") || "";

      if (!Name || !email_id || !phone_number || !password) {
        showAlert(alertBox, "Fill in every field to continue.");
        return;
      }
      if (password.length < 6) {
        showAlert(alertBox, "Password should be at least 6 characters.");
        return;
      }
      if (password !== confirmPassword) {
        showAlert(alertBox, "Passwords don't match.");
        return;
      }

      setLoading(submitBtn, true);
      try {
        // Backend schema (AdminRegister) expects the capitalized "Name" key —
        // this is intentional, not a typo.
        await api("/admin/register", {
          method: "POST",
          json: { Name, email_id, phone_number, password },
        });
        window.location.href = "login.html?registered=1";
      } catch (err) {
        showAlert(alertBox, err.message || "Could not create the account.");
      } finally {
        setLoading(submitBtn, false, "Create account");
      }
    });
  }
})();
