"""
Módulo de Autenticação Administrativa — OTTO Atlas Gen 4.0
----------------------------------------------------------
Valida tokens Firebase JWT e restringe acesso ao email do administrador.
Usado como dependência FastAPI (Depends) nos endpoints destrutivos.

Requisito: google-auth no requirements.txt
Env vars necessárias no Render:
  FIREBASE_PROJECT_ID  → otto-ecosystem
  ADMIN_EMAIL          → dr.dhsig@gmail.com  (default já definido)
"""

import os
from fastapi import Header, HTTPException, Depends

FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "otto-ecosystem")
ADMIN_EMAILS = {os.environ.get("ADMIN_EMAIL", "dr.dhsig@gmail.com")}


def verify_admin(authorization: str = Header(default=None)):
    """
    Dependência FastAPI que valida o Firebase idToken enviado no header
    Authorization: Bearer <token>

    Retorna o email do admin autenticado se válido.
    Lança 401 se token ausente/inválido, 403 se email não autorizado.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Autenticação necessária. Faça login como administrador."
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token vazio.")

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        # Verifica assinatura JWT contra chaves públicas do Google (cache automático)
        claims = id_token.verify_firebase_token(
            token,
            google_requests.Request(),
            audience=FIREBASE_PROJECT_ID
        )

        email = claims.get("email", "")
        if not email:
            raise HTTPException(status_code=401, detail="Token sem email associado.")

        if email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=403,
                detail=f"Conta '{email}' não autorizada como administrador do Atlas."
            )

        return email

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado. Faça login novamente."
        )
