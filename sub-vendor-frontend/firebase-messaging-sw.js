importScripts("https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js");

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

firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || "Expense Management";
  const options = {
    body: payload.notification?.body || "You have a new notification.",
    icon: "/favicon.ico",
  };
  self.registration.showNotification(title, options);
});
