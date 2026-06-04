"""
Script de Deploy do Modelo OTOSCOP-IA para o Render.
Faz upload do otto_model.onnx + vocab.txt + training_metadata.json
via rota protegida /api/admin/model/upload.

Requer Firebase Auth token do admin.

Uso:
  python deploy_model.py
"""
import os
import sys
import json

# Pedir a URL do backend
RENDER_URL = os.environ.get(
    "RENDER_BACKEND_URL",
    "https://otto-atlas.onrender.com"  # ajustar se diferente
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
ONNX_PATH = os.path.join(MODELS_DIR, "otto_model.onnx")
VOCAB_PATH = os.path.join(MODELS_DIR, "vocab.txt")
META_PATH = os.path.join(MODELS_DIR, "training_metadata.json")

def get_firebase_token():
    """
    Obtém token Firebase do admin para autenticar a rota protegida.
    Requer o pacote firebase-admin ou token manual.
    """
    # Tenta usar token salvo em variável de ambiente
    token = os.environ.get("FIREBASE_ID_TOKEN")
    if token:
        return token
    
    # Caso contrário, pede no terminal
    print("\n[AUTH] Token Firebase ID necessário para autenticar como admin.")
    print("       Obtenha via: Firebase Console > Authentication > seu usuário")
    print("       Ou cole o token do DevTools do browser (Network > Authorization header)")
    token = input("\nCole o Firebase ID Token aqui: ").strip()
    if not token:
        print("[ERRO] Token vazio. Abortando.")
        sys.exit(1)
    return token


def main():
    import requests
    
    print("=" * 60)
    print("OTOSCOP-IA — Deploy de Modelo para Render")
    print("=" * 60)
    print(f"Backend:  {RENDER_URL}")
    print(f"Modelo:   {ONNX_PATH}")
    print()
    
    # Verificar arquivos
    if not os.path.exists(ONNX_PATH):
        print(f"[ERRO] Modelo ONNX não encontrado: {ONNX_PATH}")
        print("       Rode train_model.py e export_onnx.py primeiro.")
        sys.exit(1)
    
    if not os.path.exists(VOCAB_PATH):
        print(f"[ERRO] vocab.txt não encontrado: {VOCAB_PATH}")
        sys.exit(1)
    
    onnx_size = os.path.getsize(ONNX_PATH) / 1024 / 1024
    print(f"[INFO] otto_model.onnx: {onnx_size:.1f} MB")
    print(f"[INFO] vocab.txt: {os.path.getsize(VOCAB_PATH)} bytes")
    
    # Ler vocab para confirmar
    with open(VOCAB_PATH, "r", encoding="utf-8") as f:
        vocab = [l.strip() for l in f if l.strip()]
    print(f"[INFO] Classes ({len(vocab)}): {', '.join(vocab)}")
    
    # Ler metadata se existir
    if os.path.exists(META_PATH):
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        print(f"[INFO] Treinado em: {meta.get('trained_at', '?')}")
        print(f"[INFO] Arquitetura: {meta.get('architecture', '?')}")
    
    print()
    confirm = input("Prosseguir com o upload? (s/N): ").strip().lower()
    if confirm != 's':
        print("Cancelado.")
        sys.exit(0)
    
    # Auth
    token = get_firebase_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Checar saúde do backend
    print("\n[1/3] Verificando saúde do backend...")
    try:
        r = requests.get(f"{RENDER_URL}/health", timeout=30)
        print(f"       Status: {r.json()}")
    except Exception as e:
        print(f"       [WARN] Backend pode estar acordando: {e}")
        print("       Aguarde 30s e tente novamente se falhar.")
    
    # 2. Upload do modelo
    print("\n[2/3] Enviando modelo ONNX + vocab.txt...")
    
    with open(ONNX_PATH, "rb") as onnx_f, open(VOCAB_PATH, "rb") as vocab_f:
        files = {
            "onnx_file": ("otto_model.onnx", onnx_f, "application/octet-stream"),
            "vocab_file": ("vocab.txt", vocab_f, "text/plain"),
        }
        
        try:
            r = requests.post(
                f"{RENDER_URL}/api/admin/model/upload",
                headers=headers,
                files=files,
                timeout=120  # Upload de 44MB pode levar tempo
            )
            
            if r.status_code == 200:
                result = r.json()
                if result.get("success"):
                    print(f"       [OK] {result['message']}")
                    print(f"       Arquivos: {result['files']}")
                else:
                    print(f"       [ERRO] {result}")
                    sys.exit(1)
            else:
                print(f"       [ERRO] HTTP {r.status_code}: {r.text[:500]}")
                sys.exit(1)
                
        except requests.exceptions.Timeout:
            print("       [ERRO] Timeout no upload. O Render free tier pode ter limitações.")
            print("       Considere usar o Render Shell: render shell > copiar para /var/data/")
            sys.exit(1)
    
    # 3. Verificar modelo deployado
    print("\n[3/3] Verificando modelo deployado...")
    try:
        r = requests.get(
            f"{RENDER_URL}/api/admin/model/info",
            headers=headers,
            timeout=30
        )
        if r.status_code == 200:
            info = r.json()
            print(f"       Dir: {info.get('base_dir')}")
            print(f"       Modelo: {info.get('model_size_mb', '?')} MB")
            print(f"       Vocab: {info.get('vocab', [])}")
            print(f"       Session loaded: {info.get('session_loaded')}")
        else:
            print(f"       [WARN] Não foi possível verificar: HTTP {r.status_code}")
    except Exception as e:
        print(f"       [WARN] {e}")
    
    print()
    print("=" * 60)
    print("[OK] Deploy concluído! Teste com uma imagem no OTOSCOP-IA.")
    print("=" * 60)


if __name__ == "__main__":
    main()
