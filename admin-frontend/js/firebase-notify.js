import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging.js";

// Keep this in sync with app/firebase/firebase_config.py / .env FIREBASE_PROJECT_ID
const firebaseConfig = {
  apiKey: "AIzaSyAw3OXhbhci1IUV-IhEN_dn2j2Z7R9dDuQ",
  authDomain: "expense-management-syste-b7da5.firebaseapp.com",
  projectId: "expense-management-syste-b7da5",
  storageBucket: "expense-management-syste-b7da5.firebasestorage.app",
  messagingSenderId: "751535863751",
  appId: "1:751535863751:web:ab3f5e14b43eca354d0be2",
  measurementId: "G-17CECSNVV4",
};

const VAPID_KEY =
  "BAPtgMHsJmyjO24dR6YqIM6mrRlVNSQ-qNeqa6UYQ0DkEEhYP1l9scseeU0JOGkVUh2c7Vw9QhyPribc-wP4w3s";

const $ = (sel, root = document) => root.querySelector(sel);

function toast(message, type = "default") {
  const stack = $("#toastStack");
  if (!stack) return;
  const el = document.createElement("div");
  el.className = "toast" + (type === "error" ? " toast-error" : type === "success" ? " toast-success" : "");
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(() => el.remove(), 3600);
}

const NOTIF_STORAGE_KEY = "ledger_admin_notifications";

function loadStoredNotifications() {
  try {
    return JSON.parse(sessionStorage.getItem(NOTIF_STORAGE_KEY) || "[]");
  } catch (_) {
    return [];
  }
}

function saveStoredNotifications(list) {
  try {
    sessionStorage.setItem(NOTIF_STORAGE_KEY, JSON.stringify(list.slice(0, 30)));
  } catch (_) { /* ignore quota errors */ }
}

let notifications = loadStoredNotifications();

function renderNotifPanel() {
  const body = $("#notifPanelBody");
  const badge = $("#notifBadge");
  if (!body) return;

  if (notifications.length === 0) {
    body.innerHTML = '<p class="empty-mini">No notifications yet. Enable push to get live updates from sub-vendors.</p>';
  } else {
    body.innerHTML = notifications
      .map(
        (n) => `
        <div class="notif-item">
          <div class="notif-item-title">${escapeHtml(n.title)}</div>
          <div>${escapeHtml(n.body)}</div>
          <div class="notif-item-time">${new Date(n.at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</div>
        </div>`
      )
      .join("");
  }

  if (badge) {
    if (notifications.length > 0) {
      badge.hidden = false;
      badge.textContent = notifications.length > 9 ? "9+" : String(notifications.length);
    } else {
      badge.hidden = true;
    }
  }
}

function escapeHtml(str) {
  return String(str == null ? "" : str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function addNotification(title, body) {
  notifications.unshift({ title, body, at: Date.now() });
  notifications = notifications.slice(0, 30);
  saveStoredNotifications(notifications);
  renderNotifPanel();

  if (typeof window.__refreshVendorRequestCounts === "function") {
    window.__refreshVendorRequestCounts();
  }
}

renderNotifPanel();

/* Bell + panel toggling */
const bell = $("#notifBell");
const panel = $("#notifPanel");
if (bell && panel) {
  bell.addEventListener("click", (e) => {
    e.stopPropagation();
    panel.hidden = !panel.hidden;
  });
  document.addEventListener("click", (e) => {
    if (!panel.hidden && !panel.contains(e.target) && e.target !== bell) {
      panel.hidden = true;
    }
  });
}

const clearBtn = $("#notifClearBtn");
if (clearBtn) {
  clearBtn.addEventListener("click", () => {
    notifications = [];
    saveStoredNotifications(notifications);
    renderNotifPanel();
  });
}

/* ----------------------------------------------------------
   Firebase setup
---------------------------------------------------------- */
const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

async function enablePushNotifications() {
  try {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      toast("Notification permission was not granted", "error");
      return;
    }

    const registration = await navigator.serviceWorker.register("firebase-messaging-sw.js");

    const token = await getToken(messaging, {
      vapidKey: VAPID_KEY,
      serviceWorkerRegistration: registration,
    });

    if (!token) {
      toast("Could not generate a push token", "error");
      return;
    }

    const adminIdInput = $("#adminIdInput");
    const userId = Number((adminIdInput && adminIdInput.value) || 1);

    await fetch("/notifications/register-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, device_token: token }),
    });

    toast("Push alerts enabled for this admin account", "success");
  } catch (err) {
    console.error("Firebase push setup failed:", err);
    toast("Could not enable push alerts: " + err.message, "error");
  }
}

const enableBtn = $("#enableNotifBtn");
if (enableBtn) {
  enableBtn.addEventListener("click", enablePushNotifications);
}

/* Foreground messages: sub-vendor actions arriving while the
   admin panel is open. */
onMessage(messaging, (payload) => {
  const title = payload.notification?.title || "Update";
  const body = payload.notification?.body || "";
  addNotification(title, body);
  toast(`${title}: ${body}`);
});
