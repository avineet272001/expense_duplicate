/* ============================================================
   Auth module — Ledger Vendor
   ------------------------------------------------------------
   HOW TO CONNECT THIS TO YOUR BACKEND
   Edit the CONFIG block below. Nothing else in this file
   should need to change for most JWT-style login APIs.
   ============================================================ */

const AUTH_CONFIG = {
  // Base URL for API calls. Leave "" if the frontend is served
  // by the same FastAPI app as the API (same-origin), matching
  // app.js's own API constant.
  API_BASE: "",

  // Endpoint your backend exposes for login.
  LOGIN_ENDPOINT: "/auth/login",

  // Endpoint for logout. Set to null if your backend has none
  // (client-side token removal only).
  LOGOUT_ENDPOINT: null,

  // What the login request body looks like. Change the KEYS
  // (left side) to match your backend's expected field names.
  // e.g. if your backend expects {email, password}, change
  // "username" below to "email".
  buildLoginPayload(username, password) {
    return {
      username: username,   // <-- change key name if backend expects "email" / "vendor_id" etc.
      password: password,
    };
  },

  // How to pull data out of a successful login response.
  // Adjust these paths to match your backend's response shape.
  parseLoginResponse(data) {
    return {
      token: data.access_token || data.token,
      tokenType: data.token_type || "Bearer",
      vendorId: data.vendor_id ?? data.user?.vendor_id ?? data.user?.id ?? null,
      name: data.name ?? data.user?.name ?? data.username ?? null,
    };
  },

  // localStorage / sessionStorage key.
  STORAGE_KEY: "ledger_auth",

  // Where to send an unauthenticated user.
  LOGIN_PAGE: "login.html",

  // Where to send a user after a successful login.
  APP_PAGE: "index.html",
};

/* ----------------------------------------------------------
   Storage helpers — supports "remember me" (localStorage)
   vs session-only (sessionStorage)
---------------------------------------------------------- */
const Auth = (() => {
  function getStore() {
    // Prefer whichever storage actually has the session.
    if (sessionStorage.getItem(AUTH_CONFIG.STORAGE_KEY)) return sessionStorage;
    return localStorage;
  }

  function save(session, remember) {
    const store = remember ? localStorage : sessionStorage;
    const other = remember ? sessionStorage : localStorage;
    other.removeItem(AUTH_CONFIG.STORAGE_KEY); // avoid stale copies in both stores
    store.setItem(AUTH_CONFIG.STORAGE_KEY, JSON.stringify(session));
  }

  function read() {
    try {
      const raw = getStore().getItem(AUTH_CONFIG.STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  }

  function clear() {
    localStorage.removeItem(AUTH_CONFIG.STORAGE_KEY);
    sessionStorage.removeItem(AUTH_CONFIG.STORAGE_KEY);
  }

  function isLoggedIn() {
    const s = read();
    return !!(s && s.token);
  }

  function getToken() {
    const s = read();
    return s ? s.token : null;
  }

  function getVendorId() {
    const s = read();
    return s ? s.vendorId : null;
  }

  function getName() {
    const s = read();
    return s ? s.name : null;
  }

  // Header object to spread into any fetch() call's headers.
  function authHeader() {
    const s = read();
    if (!s || !s.token) return {};
    return { Authorization: `${s.tokenType || "Bearer"} ${s.token}` };
  }

  async function login(username, password, remember = true) {
    const res = await fetch(AUTH_CONFIG.API_BASE + AUTH_CONFIG.LOGIN_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(AUTH_CONFIG.buildLoginPayload(username, password)),
    });

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || body.message || detail;
      } catch (_) { /* ignore */ }
      throw new Error(typeof detail === "string" ? detail : "Login failed");
    }

    const data = await res.json();
    const parsed = AUTH_CONFIG.parseLoginResponse(data);
    if (!parsed.token) {
      throw new Error("Login response did not include a token — check parseLoginResponse() in auth.js");
    }
    save(parsed, remember);
    return parsed;
  }

  async function logout() {
    if (AUTH_CONFIG.LOGOUT_ENDPOINT) {
      try {
        await fetch(AUTH_CONFIG.API_BASE + AUTH_CONFIG.LOGOUT_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeader() },
        });
      } catch (_) { /* best-effort */ }
    }
    clear();
    window.location.href = AUTH_CONFIG.LOGIN_PAGE;
  }

  // Call at the very top of a protected page to bounce
  // unauthenticated visitors to the login page.
  function requireAuth() {
    if (!isLoggedIn()) {
      window.location.href = AUTH_CONFIG.LOGIN_PAGE;
    }
  }

  // Call at the top of login.html to skip straight to the app
  // if already signed in.
  function redirectIfLoggedIn() {
    if (isLoggedIn()) {
      window.location.href = AUTH_CONFIG.APP_PAGE;
    }
  }

  return {
    login,
    logout,
    isLoggedIn,
    getToken,
    getVendorId,
    getName,
    authHeader,
    requireAuth,
    redirectIfLoggedIn,
  };
})();

/* ----------------------------------------------------------
   Wire up the login form (only present on login.html)
---------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  Auth.redirectIfLoggedIn();

  const form = document.getElementById("loginForm");
  if (!form) return; // not on the login page

  const alertBox = document.getElementById("loginAlert");
  const submitBtn = document.getElementById("loginSubmit");
  const submitText = document.getElementById("loginSubmitText");
  const toggleBtn = document.getElementById("togglePassword");
  const passwordInput = document.getElementById("loginPassword");

  toggleBtn?.addEventListener("click", () => {
    const isHidden = passwordInput.type === "password";
    passwordInput.type = isHidden ? "text" : "password";
    toggleBtn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
  });

  function showError(message) {
    alertBox.textContent = message;
    alertBox.hidden = false;
  }
  function hideError() {
    alertBox.hidden = true;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();

    const username = document.getElementById("loginUsername").value.trim();
    const password = passwordInput.value;
    const remember = document.getElementById("rememberMe").checked;

    if (!username || !password) {
      showError("Please enter both your username/email and password.");
      return;
    }

    submitBtn.disabled = true;
    submitText.textContent = "Signing in…";

    try {
      await Auth.login(username, password, remember);
      window.location.href = AUTH_CONFIG.APP_PAGE;
    } catch (err) {
      showError(err.message || "Could not sign in. Check your credentials and try again.");
      submitBtn.disabled = false;
      submitText.textContent = "Sign in";
    }
  });
});
