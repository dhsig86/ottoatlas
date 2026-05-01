/**
 * adminAuth.ts — Autenticação administrativa via Google/Firebase
 *
 * Guarda o idToken em memória e o renova automaticamente.
 * Qualquer componente chama getAuthHeaders() para incluir o token nas requests.
 */

import {
  GoogleAuthProvider,
  signInWithPopup,
  signOut as firebaseSignOut,
  onIdTokenChanged,
  type User,
} from "firebase/auth";
import { auth } from "../lib/firebase";

// Email autorizado como administrador
const ADMIN_EMAIL = import.meta.env.VITE_ADMIN_EMAIL || "dr.dhsig@gmail.com";

// Token em memória — renovado automaticamente pelo Firebase a cada ~55 min
let _token: string | null = null;
let _adminEmail: string | null = null;

// Escuta mudanças de token e renova automaticamente
onIdTokenChanged(auth, async (user: User | null) => {
  if (user && user.email === ADMIN_EMAIL) {
    _token = await user.getIdToken();
    _adminEmail = user.email;
  } else {
    _token = null;
    _adminEmail = null;
  }
});

/** Retorna headers com Bearer token, se autenticado. */
export function getAuthHeaders(): HeadersInit {
  return _token ? { Authorization: `Bearer ${_token}` } : {};
}

/** Retorna o email do admin logado, ou null. */
export function getAdminEmail(): string | null {
  return _adminEmail;
}

/** Login com popup Google. Retorna email se autorizado, lança erro se não. */
export async function signInWithGoogle(): Promise<string> {
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });

  const result = await signInWithPopup(auth, provider);
  const user = result.user;

  if (user.email !== ADMIN_EMAIL) {
    await firebaseSignOut(auth);
    throw new Error(`Conta ${user.email} não autorizada como administrador.`);
  }

  _token = await user.getIdToken();
  _adminEmail = user.email;
  return user.email || "";
}

/** Logout. */
export async function signOut(): Promise<void> {
  await firebaseSignOut(auth);
  _token = null;
  _adminEmail = null;
}

/** Verifica se já há sessão ativa do admin ao carregar a página. */
export async function checkExistingSession(): Promise<string | null> {
  return new Promise((resolve) => {
    const unsubscribe = onIdTokenChanged(auth, async (user) => {
      unsubscribe();
      if (user && user.email === ADMIN_EMAIL) {
        _token = await user.getIdToken();
        _adminEmail = user.email;
        resolve(user.email);
      } else {
        resolve(null);
      }
    });
  });
}
