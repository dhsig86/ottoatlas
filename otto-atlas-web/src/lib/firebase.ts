import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey:            import.meta.env.VITE_FIREBASE_API_KEY || "REVOGADA_USE_ENV_VARS",
  authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "otto-ecosystem.firebaseapp.com",
  projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID || "otto-ecosystem",
  storageBucket:     import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "otto-ecosystem.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "767979353790",
  appId:             import.meta.env.VITE_FIREBASE_APP_ID || "1:767979353790:web:1ad09ef2243149199150ef",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
