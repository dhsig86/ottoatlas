from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
import pathlib
from PIL import Image
import io
import time
import hashlib
import requests
import unicodedata
import re

try:
    from ml_pipeline.auth import verify_admin
except ModuleNotFoundError:
    from auth import verify_admin  # type: ignore


def normalize_class_name(name: str) -> str:
    """
    Sanitiza um nome de classe para armazenamento no backend e modelo ML.
    Remove acentos, caracteres especiais, força snake_case lowercase.
    Exemplo: "Otite Média Aguda" → "otite_media_aguda"
    O display formatado (com acentos, title-case) fica exclusivamente no frontend.
    """
    n = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    n = re.sub(r'[^a-zA-Z0-9\s_]', '', n)
    return '_'.join(n.lower().split())

def get_database_url():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    return line.strip().split("=", 1)[1]
    return os.environ.get("DATABASE_URL")

cloudinary_config = {"cloud_name": None, "api_key": None, "api_secret": None}

def setup_cloudinary():
    global cloudinary_config
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    c_url = os.environ.get("CLOUDINARY_URL")
    if not c_url and os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("CLOUDINARY_URL="):
                    c_url = line.strip().split("=", 1)[1]
                    break
    if c_url:
        os.environ["CLOUDINARY_URL"] = c_url
        try:
            url_no_prefix = c_url.replace("cloudinary://", "")
            api_key, rest = url_no_prefix.split(":", 1)
            api_secret, cloud_name = rest.split("@", 1)
            cloudinary_config["api_key"] = api_key
            cloudinary_config["api_secret"] = api_secret
            cloudinary_config["cloud_name"] = cloud_name
            return True
        except Exception:
            return False
    return False

def upload_to_cloudinary_rest(file_contents, folder):
    global cloudinary_config
    
    if not cloudinary_config.get("cloud_name"):
        setup_cloudinary()
        
    cloud_name = cloudinary_config.get("cloud_name")
    api_key = cloudinary_config.get("api_key")
    api_secret = cloudinary_config.get("api_secret")
    
    if not cloud_name or not api_key or not api_secret:
        raise Exception("Cloudinary variables are not properly loaded.")

    timestamp = str(int(time.time()))
    files = {'file': ('image.jpg', file_contents, 'image/jpeg')}
    
    params_to_sign = f"folder={folder}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(params_to_sign.encode('utf-8')).hexdigest()

    data = {
        'api_key': api_key,
        'timestamp': timestamp,
        'folder': folder,
        'signature': signature
    }
    
    url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    response = requests.post(url, data=data, files=files, timeout=60)
    
    if response.status_code == 200:
        return response.json().get("secure_url")
    else:
        raise Exception(f"Cloudinary REST API Error HTTP {response.status_code}: {response.text}")

app = FastAPI(title="OTOSCOP-IA Engine", description="FastAPI Backend for ONNX Runtime")

# Permitir o Frontend React (dev + produção + PWA iframe)
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://localhost:5174",
    "http://localhost:5175",
    "https://otto.drdariohart.com",
    "https://ottopwa.vercel.app",
    "https://ottos-plum.vercel.app",
    "https://atlas.drdariohart.com",
    "https://otto-ecosystem.web.app",
    "https://otto-ecosystem.firebaseapp.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    # Contexto: rodando da raiz do repo (uvicorn ml_pipeline.main:app)
    from ml_pipeline.routers.cms import router as cms_router
except ModuleNotFoundError:
    # Contexto: Render com Root Directory = ml_pipeline/ (uvicorn main:app)
    from routers.cms import router as cms_router  # type: ignore
app.include_router(cms_router)


@app.get("/health", tags=["System"])
def health_check():
    """Health check para o Render.com monitorar o serviço."""
    return {"status": "ok", "model_loaded": ort_session is not None}

# Variáveis de Memória Ultraleves (Apenas ONNX Session e Array de Strings)
ort_session = None
vocab = []


def lazy_load_model():
    global ort_session, vocab
    if ort_session is not None:
        return
        
    import onnxruntime as ort

    # Em produção (Render Starter Disk), o modelo fica em /var/data
    # Em desenvolvimento local, fica em ml_pipeline/models/
    RENDER_DISK_PATH = "/var/data"
    LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    BASE_DIR = RENDER_DISK_PATH if os.path.isdir(RENDER_DISK_PATH) else LOCAL_PATH

    model_path = os.path.join(BASE_DIR, "otto_model.onnx")
    vocab_path = os.path.join(BASE_DIR, "vocab.txt")
    print(f"Carregando ONNX de: {BASE_DIR}")
    
    if os.path.exists(model_path) and os.path.exists(vocab_path):
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                vocab = [line.strip() for line in f if line.strip()]
            
            opts = ort.SessionOptions()
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
            
            ort_session = ort.InferenceSession(model_path, sess_options=opts, providers=['CPUExecutionProvider'])
            print(f"Sucesso! Cérebro ONNX Carregado. Vocabulário: {vocab}")
        except Exception as e:
            print(f"Erro Fatal ONNX: {e}")
    else:
        print(f"Alerta: Modelo ONNX não encontrado em {BASE_DIR}. Verifique o Render Disk ou ml_pipeline/models/.")


KAGGLE_VOCAB_TO_CANONICAL = {
    "CERUME OBSTRUCAO": "cerume_obstrucao",
    "CERUME OBSTRUÇÃO": "cerume_obstrucao",
    "CERUME_OBSTRUCAO": "cerume_obstrucao",
    "NAO OTOSCOPICA": "nao_otoscopica",
    "NAO_OTOSCOPICA": "nao_otoscopica",
    "NORMAL": "normal",
    "NORMAL (100%)": "normal",
    "NORMAL (39%)": "normal",
    "NORMAL (48%)": "normal",
    "NORMAL (49%)": "normal",
    "NORMAL (55%)": "normal",
    "NORMAL (61%)": "normal",
    "NORMAL (72%)": "normal",
    "NORMAL (76%)": "normal",
    "NORMAL (77%)": "normal",
    "NORMAL (86%)": "normal",
    "NORMAL (87%)": "normal",
    "NORMAL (96%)": "normal",
    "NORMAL (97%)": "normal",
    "NORMAL (98%)": "normal",
    "NORMAL (99%)": "normal",
    "NORMAL_100_OTITE_MEDIA_CRONICA_0_NAO_OTOSCOPICA_0": "normal",
    "NORMAL_100_OTITE_MEDIA_CRONICA_0_OBSTRUCAO_0": "normal",
    "NORMAL_100_OTITE_MEDIA_CRONICA_0_OTITE_MEDIA_AGUDA_0": "normal",
    "NORMAL_59_NAO_OTOSCOPICA_36_OTITE_EXTERNA_AGUDA_4": "normal",
    "NORMAL_75_OTITE_MEDIA_CRONICA_24_NAO_OTOSCOPICA_0": "normal",
    "NORMAL_78_OTITE_EXTERNA_AGUDA_14_OTITE_MEDIA_CRONICA_6": "normal",
    "NORMAL_89_OTITE_MEDIA_CRONICA_9_OTITE_EXTERNA_AGUDA_2": "normal",
    "NORMAL_97_OTITE_MEDIA_CRONICA_2_OTITE_EXTERNA_AGUDA_1": "normal",
    "OBSTRUCAO (53%), OTITE EXTERNA AGUDA (25%), NAO OTOSCOPICA (21%)": "cerume_obstrucao",
    "OBSTRUCAO (78%)": "cerume_obstrucao",
    "OBSTRUCAO_53_OTITE_EXTERNA_AGUDA_25_NAO_OTOSCOPICA_21": "cerume_obstrucao",
    "OSTEOMAS": "cerume_obstrucao",
    "OSTEOMAS_E_EXOSTOSE": "cerume_obstrucao",
    "OTITE EXTERNA AGUDA": "otite_externa_aguda",
    "OTITE EXTERNA AGUDA (79%)": "otite_externa_aguda",
    "OTITE EXTERNA AGUDA (89%), NAO OTOSCOPICA (6%), OBSTRUCAO (4%)": "otite_externa_aguda",
    "OTITE EXTERNA DESCAMATIVA": "otite_externa_aguda",
    "OTITE MEDIA AGUDA": "otite_media_aguda",
    "OTITE MEDIA CRONICA": "otite_media_cronica",
    "OTITE MEDIA CRONICA (97%)": "otite_media_cronica",
    "OTITE MÉDIA AGUDA": "otite_media_aguda",
    "OTITE MÉDIA CRÔNICA ATELECTÁSICA": "otite_media_cronica",
    "OTITE MÉDIA CRÔNICA SIMPLES": "otite_media_cronica",
    "OTITE_EXTERNA_AGUDA": "otite_externa_aguda",
    "OTITE_EXTERNA_AGUDA_89_NAO_OTOSCOPICA_6_OBSTRUCAO_4": "otite_externa_aguda",
    "OTITE_MEDIA_AGUDA": "otite_media_aguda",
    "OTITE_MEDIA_CRONICA": "otite_media_cronica",
    "TIMPANOESCLEROSE": "timpanoesclerose",
    "TUBO DE VENTILACAO": "tubo_de_ventilacao",
    "TUBO_DE_VENTILACAO": "tubo_de_ventilacao",
    "_DISCARD_": "_DISCARD_"
}

DISPLAY_NAMES = {
    "cerume_obstrucao":     "Cerume / Obstrução",
    "nao_otoscopica":       "Não Otoscópica",
    "normal":               "Normal",
    "otite_externa_aguda":  "Otite Externa Aguda",
    "otite_media_aguda":    "Otite Média Aguda",
    "otite_media_cronica":  "Otite Média Crônica",
    "otite_media_serosa":   "Otite Média Serosa",
    "timpanoesclerose":     "Timpanoesclerose",
    "tubo_de_ventilacao":   "Tubo de Ventilação",
}


@app.post("/api/predict")
def predict_image(file: UploadFile = File(...)):
    lazy_load_model()
    if not ort_session or not vocab:
        return {"error": "O cérebro ONNX não está carregado. Verifique os logs do servidor."}
    
    contents = file.file.read()
    
    try:
        import numpy as np
        # Pre-processamento rigoroso de imagens matriciais ao estilo FastAI (3x224x224 RGB)
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        img = img.resize((224, 224), Image.Resampling.BILINEAR)
        
        # Desmontando Imagem para Tensores Float Baseados em [0..1]
        img_arr = np.array(img).astype(np.float32) / 255.0
        
        # ImageNet Normalization Padrão do PyTorch
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_arr = (img_arr - mean) / std
        
        # O PyTorch Treinou como [Channels, Height, Width]! Então o eixo da Imagem precisa virar
        img_arr = np.transpose(img_arr, (2, 0, 1))
        # Fabricar Lote [Batch(=1), Channels(=3), Height(=224), Width(=224)]
        input_tensor = np.expand_dims(img_arr, axis=0)
        
        # Roda inferência de C++ Nativo (Milissegundos)
        inputs = {ort_session.get_inputs()[0].name: input_tensor}
        logits = ort_session.run(None, inputs)[0][0]
        
        # Calibragem matemática Softmax (Distribuição Probabilística de 0 a 1)
        exp_L = np.exp(logits - np.max(logits))
        probs = exp_L / np.sum(exp_L)
        
        # Inicializa o dicionário de probabilidades canônicas zerado
        canonical_probs = {k: 0.0 for k in DISPLAY_NAMES.keys()}
        
        # Agrupa e soma as probabilidades
        for v, p in zip(vocab, probs):
            canonical_class = KAGGLE_VOCAB_TO_CANONICAL.get(v, "_DISCARD_")
            if canonical_class != "_DISCARD_":
                if canonical_class in canonical_probs:
                    canonical_probs[canonical_class] += float(p)
        
        # Renormaliza as probabilidades para que a soma dos válidos seja exatamente 1.0
        total_sum = sum(canonical_probs.values())
        if total_sum > 0:
            for k in canonical_probs:
                canonical_probs[k] /= total_sum
                
        # Combina classes com probabilidades e ordena
        predictions = [
            {"class": DISPLAY_NAMES[key], "confidence": round(canonical_probs[key] * 100, 1)}
            for key in canonical_probs
        ]
        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "predictions": predictions[:5],
            "disclaimer": "Sugestão baseada exclusivamente na imagem. Não substitui avaliação clínica completa (anamnese, otoscopia dinâmica, exame físico).",
            "model_version": "v3.0-resnet18-kaggle"
        }
        

def get_gemini_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        os.environ["GEMINI_API_KEY"] = key
                        break
    return key


@app.post("/api/predict/confronto")
def predict_confronto(file: UploadFile = File(...)):
    lazy_load_model()
    if not ort_session or not vocab:
        return {"error": "O cérebro ONNX não está carregado. Verifique os logs do servidor."}
    
    contents = file.file.read()
    
    local_predictions = []
    local_error = None
    try:
        import numpy as np
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        img_resized = img.resize((224, 224), Image.Resampling.BILINEAR)
        img_arr = np.array(img_resized).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_arr = (img_arr - mean) / std
        img_arr = np.transpose(img_arr, (2, 0, 1))
        input_tensor = np.expand_dims(img_arr, axis=0)
        
        inputs = {ort_session.get_inputs()[0].name: input_tensor}
        logits = ort_session.run(None, inputs)[0][0]
        
        exp_L = np.exp(logits - np.max(logits))
        probs = exp_L / np.sum(exp_L)
        
        canonical_probs = {k: 0.0 for k in DISPLAY_NAMES.keys()}
        for v, p in zip(vocab, probs):
            canonical_class = KAGGLE_VOCAB_TO_CANONICAL.get(v, "_DISCARD_")
            if canonical_class != "_DISCARD_":
                if canonical_class in canonical_probs:
                    canonical_probs[canonical_class] += float(p)
        
        total_sum = sum(canonical_probs.values())
        if total_sum > 0:
            for k in canonical_probs:
                canonical_probs[k] /= total_sum
                
        local_predictions = [
            {"class": DISPLAY_NAMES[key], "confidence": round(canonical_probs[key] * 100, 1)}
            for key in canonical_probs
        ]
        local_predictions.sort(key=lambda x: x["confidence"], reverse=True)
        local_predictions = local_predictions[:5]
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        local_error = f"Falha na inferência local ONNX: {str(e)}"

    gemini_key = get_gemini_api_key()
    gemini_response = ""
    gemini_error = None
    
    if gemini_key:
        try:
            import base64
            img_b64 = base64.b64encode(contents).decode("utf-8")
            
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            
            headers = {"Content-Type": "application/json"}
            prompt_text = (
                "Você é um renomado médico especialista em Otorrinolaringologia (ORL). "
                "Examine esta imagem otoscópica com extremo rigor científico e gere um relatório clínico estruturado. "
                "Foque na descrição detalhada dos marcos anatômicos visíveis: "
                "1. Coloração e brilho da membrana timpânica (normal, hiperêmica, opaca, presença de reflexo luminoso). "
                "2. Integridade e posição (íntegra, perfurada, abaulada, retraída, nível de transparência). "
                "3. Cabo do martelo e demais estruturas de orelha média visíveis. "
                "Conclua sugerindo a hipótese diagnóstica ORL principal de forma probabilística (ex: sinais compatíveis com Otite Média Aguda, membrana normal, obstrução por cerume, etc.). "
                "Seja técnico, conciso e redija a resposta em português do Brasil."
            )
            
            body = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt_text},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": img_b64
                                }
                            }
                        ]
                    }
                ]
            }
            
            resp = requests.post(gemini_url, headers=headers, json=body, timeout=20)
            if resp.status_code == 200:
                resp_json = resp.json()
                try:
                    gemini_response = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as e:
                    gemini_error = f"Estrutura de resposta inesperada do Gemini API: {str(e)}"
            else:
                gemini_error = f"Erro HTTP {resp.status_code} na API do Gemini: {resp.text}"
        except Exception as e:
            gemini_error = f"Falha ao chamar a API do Gemini Vision: {str(e)}"
    else:
        gemini_error = "Variável de ambiente GEMINI_API_KEY não configurada no servidor."

    return {
        "predictions_local": local_predictions,
        "local_error": local_error,
        "predictions_gemini": gemini_response,
        "gemini_error": gemini_error,
        "disclaimer": "Confronto de IAs (Otoscopia-IA ONNX vs. Gemini Vision API). Uso pedagógico e informativo de auxílio diagnóstico.",
        "model_version": "v3.0-resnet18-onnx"
    }


@app.get("/api/curadoria/pending")
def get_pending_feedback(_admin: str = Depends(verify_admin)):
    db_url = get_database_url()
    if not db_url:
        return {"error": "Database URL not found"}
    
    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("""
            SELECT id, feedback_image_url, correct_diagnosis, diagnosis_correct, predicted_classes, clinical_case
            FROM feedback
            ORDER BY id DESC LIMIT 50
        """)
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "feedback_image_url": r[1],
                "correct_diagnosis": r[2],
                "diagnosis_correct": r[3],
                "predicted_classes": r[4],
                "clinical_case": r[5]
            })
            
        cur.close()
        conn.close()
        return results
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/curadoria/auto-tag-batch")
async def auto_tag_batch(_admin: str = Depends(verify_admin)):
    """
    Percorre todos os registros da fila feedback sem predicted_classes (ex: Resgate Nuvem),
    busca a imagem Cloudinary, roda o ONNX e grava a predição top-3 na tabela.
    Isso prepara a fila para curadoria manual com sugestão de classe já visível.
    """
    lazy_load_model()
    if not ort_session or not vocab:
        return {"error": "Modelo ONNX não carregado. Verifique o Render Disk."}

    db_url = get_database_url()
    if not db_url:
        return {"error": "Database URL não encontrada."}

    import json as _json
    import numpy as np

    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()

        # Seleciona itens sem predicted_classes ou com string vazia / '""'
        cur.execute("""
            SELECT id, feedback_image_url FROM feedback
            WHERE predicted_classes IS NULL
               OR predicted_classes = ''
               OR predicted_classes = '""'
               OR predicted_classes = 'null'
            ORDER BY id DESC
            LIMIT 200
        """)
        rows = cur.fetchall()

        if not rows:
            cur.close()
            conn.close()
            return {"success": True, "tagged": 0, "message": "Nenhum item sem tag na fila."}

        tagged = 0
        failed = 0

        for (item_id, img_url) in rows:
            if not img_url or not img_url.startswith('http'):
                failed += 1
                continue
            try:
                # Busca imagem do Cloudinary
                resp = requests.get(img_url, timeout=15)
                if resp.status_code != 200:
                    failed += 1
                    continue

                # Pré-processamento idêntico ao /api/predict
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                img = img.resize((224, 224), Image.Resampling.BILINEAR)
                img_arr = np.array(img).astype(np.float32) / 255.0
                mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
                std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
                img_arr = (img_arr - mean) / std
                img_arr = np.transpose(img_arr, (2, 0, 1))
                input_tensor = np.expand_dims(img_arr, axis=0)

                inputs = {ort_session.get_inputs()[0].name: input_tensor}
                logits = ort_session.run(None, inputs)[0][0]
                exp_L = np.exp(logits - np.max(logits))
                probs = exp_L / np.sum(exp_L)

                # Inicializa probabilidades das 9 classes canônicas zeradas
                canonical_probs = {
                    "cerume_obstrucao": 0.0,
                    "nao_otoscopica": 0.0,
                    "normal": 0.0,
                    "otite_externa_aguda": 0.0,
                    "otite_media_aguda": 0.0,
                    "otite_media_cronica": 0.0,
                    "otite_media_serosa": 0.0,
                    "timpanoesclerose": 0.0,
                    "tubo_de_ventilacao": 0.0,
                }
                
                # Agrupa e soma as probabilidades
                for v, p in zip(vocab, probs.tolist()):
                    canonical_class = KAGGLE_VOCAB_TO_CANONICAL.get(v, "_DISCARD_")
                    if canonical_class != "_DISCARD_":
                        if canonical_class in canonical_probs:
                            canonical_probs[canonical_class] += p
                            
                # Renormaliza as probabilidades
                total_sum = sum(canonical_probs.values())
                if total_sum > 0:
                    for k in canonical_probs:
                        canonical_probs[k] /= total_sum

                # Top-3 classes normalizadas (sem acentos, snake_case — padrão backend)
                preds = sorted(
                    canonical_probs.items(),
                    key=lambda x: x[1], reverse=True
                )[:3]
                top_classes = ' | '.join(
                    f"{normalize_class_name(str(k))}:{p:.2f}" for k, p in preds
                )

                cur.execute(
                    "UPDATE feedback SET predicted_classes = %s WHERE id = %s",
                    (_json.dumps(top_classes), item_id)
                )
                tagged += 1

            except Exception:
                failed += 1
                continue

        conn.commit()
        cur.close()
        conn.close()

        return {
            "success": True,
            "tagged": tagged,
            "failed": failed,
            "message": f"{tagged} imagens classificadas pelo modelo. {failed} falhas (URL inválida ou timeout)."
        }

    except Exception as e:
        return {"error": str(e)}


@app.post("/api/curadoria/upload-zip")
async def process_zip_upload(file: UploadFile = File(...), _admin: str = Depends(verify_admin)):
    import zipfile
    import shutil

    if not file.filename.lower().endswith('.zip'):
        return {"error": "Por segurança, a rota de ingestão bulk aceita exclusivamente formato .zip."}
    
    # 1. Salvar na memória temporária para processamento
    temp_zip = f"temp_ingest_{int(time.time())}.zip"
    with open(temp_zip, "wb") as f:
        f.write(await file.read())
        
    try:
        # Aponte fixo para a raiz mestre de curadoria bruta
        base_dir = r"C:\Users\drdhs\OneDrive\Documentos\ottoatlas\OTTO_ML_Dataset_Raw"
        processed_count = 0
        new_classes = set()
        
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            # Navegar pelas entranhas do Zip file buscando imagens soltas nas sub-pastas
            for member in zip_ref.namelist():
                # Proteção contra diretórios fantasmas (Mac/Linux hooks)
                if member.endswith('/') or '__MACOSX' in member or '.DS_Store' in member:
                    continue
                
                parts = member.split('/')
                # A imagem tem que vir dentro de pelo menos uma "Pasta / Imagem"
                if len(parts) >= 2:
                    raw_class_name = parts[-2].strip()
                    file_name = parts[-1].strip()
                    
                    if not file_name: continue
                    
                    class_name = normalize_class_name(raw_class_name)
                    class_dir = os.path.join(base_dir, class_name)
                    if not os.path.exists(class_dir):
                        os.makedirs(class_dir, exist_ok=True)
                        new_classes.add(class_name)
                    
                    dest_file = os.path.join(class_dir, file_name)
                    
                    # Estratégia Anti-Colisão (Overwrite protection)
                    if os.path.exists(dest_file):
                        name, ext = os.path.splitext(file_name)
                        dest_file = os.path.join(class_dir, f"{name}_auto_{int(time.time()*1000)}{ext}")
                    
                    with zip_ref.open(member) as source, open(dest_file, "wb") as target:
                        shutil.copyfileobj(source, target)
                        processed_count += 1
                        
        os.remove(temp_zip)
        
        msg = f"Sucesso Crítico! {processed_count} imagens integradas ao HD."
        if new_classes:
            msg += f" O Modelo ganhou classes inéditas: {', '.join(new_classes)}."
            
        return {"success": msg}
        
    except Exception as e:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
        return {"error": f"Falha catastrófica ao processar lote: {str(e)}"}

@app.get("/api/curadoria/classes")
def get_dynamic_classes():
    """
    Rastreia dinamicamente o Vocabulário Oficial do Modelo + Quaisquer Pastas Novas 
    criadas via Front-End que ainda não foram treinadas. Retorna a lista integral!
    """
    raw_dir = r"C:\Users\drdhs\OneDrive\Documentos\ottoatlas\OTTO_ML_Dataset_Raw"
    train_dir = r"C:\Users\drdhs\OneDrive\Documentos\ottoatlas\OTTO_ML_Dataset\TRAIN"
    
    classes = set()
    global vocab
    if vocab:
        classes.update(vocab)
        
    if os.path.exists(raw_dir):
        for d in os.listdir(raw_dir):
            if os.path.isdir(os.path.join(raw_dir, d)):
                classes.add(d)
                
    if os.path.exists(train_dir):
        for d in os.listdir(train_dir):
            if os.path.isdir(os.path.join(train_dir, d)):
                classes.add(d)
                
    return {"classes": sorted(list(classes))}

@app.post("/api/curadoria/approve")
async def approve_image(payload: dict, _admin: str = Depends(verify_admin)):
    '''
    Recebe imagem da aba de Curadoria, Remove do Banco (marcando como visto),
    e se aprovada, insere no clinical_cases no NeonDB com tag 'ml_only'.
    Faz o upload no Cloudinary se a imagem for um path local.
    '''
    import time
    import json
    import os
    import cloudinary.uploader
    
    try:
        record_id = payload.get("id")
        image_url = payload.get("image_url")
        class_name = payload.get("class_name")
        is_trash = payload.get("is_trash", False)
        destination_tier = payload.get("destination_tier", "pure_ml")  # 'atlas', 'quiz', ou 'pure_ml'

        db_url = get_database_url()
        if not db_url or not record_id:
            return {"error": "Falta DB_URL ou Record ID."}

        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()

        # 1. Ler predicted_classes ANTES de deletar (para detectar correção do modelo)
        was_model_corrected = False
        cur.execute("SELECT predicted_classes FROM feedback WHERE id = %s", (record_id,))
        row = cur.fetchone()
        if row and not is_trash and class_name:
            raw_predicted = row[0] or ''
            try:
                import json as _json
                predicted_str = _json.loads(raw_predicted) if raw_predicted else ''
            except Exception:
                predicted_str = str(raw_predicted)
            # Extrai top-1 predição (pode vir como "otite_media_aguda | ..." ou só a classe)
            top_predicted = str(predicted_str).split('|')[0].split(',')[0].strip().lower()
            normalized_curator = normalize_class_name(class_name)
            normalized_predicted = normalize_class_name(top_predicted) if top_predicted else ''
            # Se curador escolheu classe diferente do modelo → candidato a retreino
            if normalized_predicted and normalized_curator != normalized_predicted:
                was_model_corrected = True

        # 2. Apagar da fila de Pendentes
        cur.execute("DELETE FROM feedback WHERE id = %s", (record_id,))
        conn.commit()

        if is_trash:
            cur.close()
            conn.close()
            return {"success": "Caso descartado da fila."}

        # 3. Normalizar classe para armazenamento (sem acentos, snake_case)
        normalized_class = normalize_class_name(class_name) if class_name else "sem_diagnostico"
        # Display title: apenas para o campo title da UI (o backend sempre armazena normalizado)
        display_title = normalized_class.replace('_', ' ').title()

        # 4. Checar a media — upar se for path local
        final_url = image_url
        if image_url and image_url.startswith("/"):
            import cloudinary.uploader
            import uuid
            src_file = os.path.join(os.path.dirname(__file__), "..", "public", image_url.lstrip("/"))
            if os.path.exists(src_file):
                new_name = f"loteML_{uuid.uuid4().hex[:8]}"
                res = cloudinary.uploader.upload(
                    src_file, folder="curadoria_gen4",
                    public_id=new_name, resource_type="image"
                )
                final_url = res.get("secure_url")
                if not final_url:
                    cur.close()
                    conn.close()
                    return {"error": "Falha upload Cloudinary do repositório local."}
                try:
                    os.remove(src_file)
                except Exception:
                    pass
            else:
                cur.close()
                conn.close()
                return {"error": "Arquivo local ausente na fila física."}

        # 5. Montar taxonomies — inclui retrain_candidate se o modelo errou
        import json
        taxonomies_arr = []
        if destination_tier == "pure_ml":
            taxonomies_arr = ["pure_ml"]
        elif destination_tier == "quiz":
            taxonomies_arr = ["quiz_only"]
        # Acervo (atlas) não recebe taxonomy → fica visível no album público
        if was_model_corrected:
            taxonomies_arr.append("retrain_candidate")

        # 6. Inserir no clinical_cases
        cur.execute("""
            INSERT INTO clinical_cases
            (title, clinical_history, primary_diagnosis, taxonomies, media_urls, svg_json)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            display_title,
            "Validado por Curadoria Assistida (MLOps). Revisão pelo Especialista pendente.",
            normalized_class,
            json.dumps(taxonomies_arr),
            json.dumps([final_url]),
            "[]"
        ))

        new_case_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        msg = f"Caso #{new_case_id} salvo como '{normalized_class}'."
        if was_model_corrected:
            msg += " Marcado como retrain_candidate (modelo corrigido pelo curador)."
        return {"success": msg, "case_id": new_case_id, "was_model_corrected": was_model_corrected}

    except Exception as e:
        return {"error": str(e)}

from fastapi import Request
from typing import List, Optional

@app.post("/api/curadoria/donate")
async def donate_image(request: Request):
    form = await request.form()
    files = form.getlist("files")
    if not files:
        # Fallback agressivo para clientes com cache antigo rodando offline via SW
        files = form.getlist("file")
        
    diagnostic = form.get("diagnostic", "Desconhecido")
    clinical_case = form.get("clinical_case", "")
    
    if not files:
        return {"error": "Nenhum arquivo de imagem foi enviado ou reconhecido pelo servidor."}
    if not setup_cloudinary():
        return {"error": "Credenciais do Cloudinary malformadas."}
        
    db_url = get_database_url()
    
    if not db_url:
        return {"error": "Banco de Dados não configurado no Servidor."}
        
    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        import json
        import cloudinary.uploader
        
        uploaded_urls = []
        for file in files:
            contents = await file.read()
            
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="otoscopia_colaboracao_externa",
                resource_type="image"
            )
            
            secure_url = upload_result.get("secure_url")
            if not secure_url:
                continue
                
            uploaded_urls.append(secure_url)
            case_info = f"[DOAÇÃO COMUNITÁRIA LOTE] {clinical_case}".strip()
            
            insert_query = """
            INSERT INTO feedback (feedback_image_url, correct_diagnosis, diagnosis_correct, predicted_classes, clinical_case)
            VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(insert_query, (secure_url, diagnostic, True, json.dumps(""), case_info))
            
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "urls": uploaded_urls, "message": f"{len(uploaded_urls)} Imagens recebidas na nuvem com sucesso!"}
        
    except Exception as e:
        return {"error": f"Erro interno da rota Donate: {str(e)}"}

@app.post("/api/curadoria/feedback")
@app.post("/api/feedback")
async def feedback_image(request: Request):
    """
    Ponto de entrada nativo central pra as predições do OTOSCOP-IA! 
    Substitui integralmente o antigo Backend do Heroku.
    """
    form = await request.form()
    feedbackImage = form.get("feedbackImage")
    correctDiagnosis = form.get("correctDiagnosis", "")
    diagnosisCorrect = form.get("diagnosisCorrect", "yes")
    predictedClasses = form.get("predictedClasses", "")
    differentialDiagnosis = form.get("differentialDiagnosis", "")
    clinicalCase = form.get("clinicalCase", "")
    
    if not feedbackImage:
        return {"error": "Imagem de feedback ausente na carga."}
    if not setup_cloudinary():
        return {"error": "Servidor não possui as variáveis Cloudinary ativadas ou estão mal formatadas."}
        
    db_url = get_database_url()
    
    if not db_url:
        return {"error": "Servidor não possui NeonDB ativadas."}
        
    try:
        contents = await feedbackImage.read()
        
        # Upload para o Cloudinary Native (REST API Bypass Windows DLLs)
        secure_url = upload_to_cloudinary_rest(contents, "otoscopia_curadoria_pendente")
        
        if not secure_url:
            return {"error": "Falha de comunicação Cloudinary API"}
            
        # Conexão NeonDB e Ingestão
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        
        import json
        
        insert_query = """
        INSERT INTO feedback (feedback_image_url, correct_diagnosis, diagnosis_correct, predicted_classes, clinical_case)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        # Consolida Diferenciais na coluna original de Predicted Classes pro Vercel renderizar lindamente 
        final_predictions = predictedClasses
        if differentialDiagnosis:
            final_predictions += f" | {differentialDiagnosis}"
            
        cur.execute(insert_query, (secure_url, correctDiagnosis, diagnosisCorrect, json.dumps(final_predictions), clinicalCase))
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True}
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": f"Internal FastAPI feedback exception: {str(e)}"}

# -------------------------------------------------------------
# GEN 3.0: ATLAS CMS - ROTAS DE DADOS NUVEM DO FRONTEND
# O frontend busca e envia novos casos direto para Nuvem(Sem estourar o limite de 500MB do Github)
# -------------------------------------------------------------

@app.get("/api/atlas")
async def get_atlas_cloud_items():
    db_url = get_database_url()
    if not db_url:
        return {"error": "Banco de Dados indisponível"}

    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("SELECT id, pathology, description, image_url, svg_json FROM atlas_cloud_items WHERE is_deleted = FALSE ORDER BY created_at DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        items = []
        for r in rows:
            items.append({
                "id": str(r[0]),
                "pathology": r[1] or "",
                "description": r[2] or "",
                "image_url": r[3] or "",
                "svg_json": r[4] or ""
            })
        return {"success": True, "items": items}

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}


@app.post("/api/admin/atlas")
async def create_atlas_cloud_item(request: Request, _admin: str = Depends(verify_admin)):
    form = await request.form()
    file = form.get("file")
    pathology = form.get("pathology", "Sem Patologia")
    description = form.get("description", "Sem descrição")
    svg_json = form.get("svg_json", "[]")

    if not file:
        return {"error": "Arquivo não encontado no POST form."}
    if not setup_cloudinary():
        return {"error": "Credenciais do Cloudinary malformadas ou indisponíveis."}

    db_url = get_database_url()
    if not db_url:
        return {"error": "DATABASE_URL do Neon não localizada."}

    try:
        import cloudinary.uploader
        contents = await file.read()

        upload_result = cloudinary.uploader.upload(
            contents,
            folder="otoscopia_atlas_nuvem",
            resource_type="image"
        )
        secure_url = upload_result.get("secure_url")
        if not secure_url:
            return {"error": "Falha silenciosa do Cloudinary - Não gerou URL."}

        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO atlas_cloud_items (pathology, description, image_url, svg_json) VALUES (%s, %s, %s, %s)",
            (pathology, description, secure_url, svg_json)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True, "url": secure_url, "message": "Atlas Cloud Atualizado!"}

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}


# -------------------------------------------------------------
# GEN 3.0: LIXEIRA ADMINISTRATIVA E SOFT DELETE
# -------------------------------------------------------------

@app.get("/api/admin/atlas/trash")
async def get_atlas_trash(_admin: str = Depends(verify_admin)):
    db_url = get_database_url()
    if not db_url: return {"error": "Banco indisponivel"}
    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("SELECT id, pathology, description, image_url, svg_json FROM atlas_cloud_items WHERE is_deleted = TRUE ORDER BY created_at DESC LIMIT 5")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        items = []
        for r in rows:
            items.append({
                "id": str(r[0]),
                "pathology": r[1] or "",
                "description": r[2] or "",
                "image_url": r[3] or "",
                "svg_json": r[4] or ""
            })
        return {"success": True, "items": items}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/admin/atlas/{item_id}")
async def soft_delete_atlas_item(item_id: int, _admin: str = Depends(verify_admin)):
    db_url = get_database_url()
    if not db_url: return {"error": "Banco indisponivel"}
    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("UPDATE atlas_cloud_items SET is_deleted = TRUE WHERE id = %s", (item_id,))
        if cur.rowcount == 0:
            return {"error": "Item não encontrado"}
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/admin/atlas/{item_id}/restore")
async def restore_atlas_item(item_id: int, _admin: str = Depends(verify_admin)):
    db_url = get_database_url()
    if not db_url: return {"error": "Banco indisponivel"}
    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("UPDATE atlas_cloud_items SET is_deleted = FALSE WHERE id = %s", (item_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}


# -------------------------------------------------------------
# DEPLOY DE MODELO — Upload protegido do ONNX + vocab para disco
# -------------------------------------------------------------

@app.post("/api/admin/model/upload")
async def upload_model(
    onnx_file: UploadFile = File(None),
    vocab_file: UploadFile = File(None),
    _admin: str = Depends(verify_admin)
):
    """
    Recebe otto_model.onnx e/ou vocab.txt via multipart form e salva no
    Render Persistent Disk (/var/data) ou fallback local (models/).
    Recarrega o modelo na próxima predição.
    """
    global ort_session, vocab

    RENDER_DISK_PATH = "/var/data"
    LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    TARGET_DIR = RENDER_DISK_PATH if os.path.isdir(RENDER_DISK_PATH) else LOCAL_PATH

    saved_files = []

    if onnx_file:
        target_path = os.path.join(TARGET_DIR, "otto_model.onnx")
        size = 0
        with open(target_path, "wb") as f:
            while chunk := await onnx_file.read(8192):
                f.write(chunk)
                size += len(chunk)
        size_mb = size / 1024 / 1024
        saved_files.append(f"otto_model.onnx ({size_mb:.1f} MB)")

    if vocab_file:
        target_path = os.path.join(TARGET_DIR, "vocab.txt")
        size = 0
        with open(target_path, "wb") as f:
            while chunk := await vocab_file.read(8192):
                f.write(chunk)
                size += len(chunk)
        size_mb = size / 1024 / 1024
        saved_files.append(f"vocab.txt ({size_mb:.3f} MB)")

    if not saved_files:
        raise HTTPException(
            status_code=400,
            detail="Nenhum arquivo enviado. Use campos 'onnx_file' e/ou 'vocab_file'."
        )

    # Invalidar modelo carregado para forçar reload na próxima predição
    ort_session = None
    vocab = []

    return {
        "success": True,
        "target_dir": TARGET_DIR,
        "files": saved_files,
        "message": f"Modelo atualizado em {TARGET_DIR}. Próxima predição usará o novo modelo."
    }


@app.get("/api/admin/model/info")
async def model_info(_admin: str = Depends(verify_admin)):
    """Retorna info do modelo atualmente deployado."""
    RENDER_DISK_PATH = "/var/data"
    LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    BASE_DIR = RENDER_DISK_PATH if os.path.isdir(RENDER_DISK_PATH) else LOCAL_PATH

    model_path = os.path.join(BASE_DIR, "otto_model.onnx")
    vocab_path = os.path.join(BASE_DIR, "vocab.txt")
    meta_path = os.path.join(BASE_DIR, "training_metadata.json")

    info = {"base_dir": BASE_DIR, "model_exists": os.path.exists(model_path)}

    if os.path.exists(model_path):
        info["model_size_mb"] = round(os.path.getsize(model_path) / 1024 / 1024, 1)

    if os.path.exists(vocab_path):
        with open(vocab_path, "r", encoding="utf-8") as f:
            info["vocab"] = [l.strip() for l in f if l.strip()]

    if os.path.exists(meta_path):
        import json as _json
        with open(meta_path, "r", encoding="utf-8") as f:
            info["metadata"] = _json.load(f)

    info["session_loaded"] = ort_session is not None

    return info


@app.post("/api/admin/atlas/{item_id}/svg")
async def update_atlas_svg(item_id: int, request: Request, _admin: str = Depends(verify_admin)):
    db_url = get_database_url()
    if not db_url: return {"error": "Banco indisponivel"}
    try:
        form = await request.form()
        svg_json = form.get("svg_json", "[]")
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("UPDATE atlas_cloud_items SET svg_json = %s WHERE id = %s", (svg_json, item_id))
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}
