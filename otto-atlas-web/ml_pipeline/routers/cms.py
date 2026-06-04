from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
import json

try:
    from ml_pipeline.main import get_database_url, setup_cloudinary, upload_to_cloudinary_rest
    from ml_pipeline.auth import verify_admin
except ModuleNotFoundError:
    from main import get_database_url, setup_cloudinary, upload_to_cloudinary_rest  # type: ignore
    from auth import verify_admin  # type: ignore


router = APIRouter(prefix="/api/cms", tags=["CMS Gen 4.0"])

class ClinicalCasePayload(BaseModel):
    title: str
    clinical_history: str = ""
    primary_diagnosis: str = ""
    patient_demographics: dict = {}
    taxonomies: list = []
    media_urls: list = []
    svg_json: str = "[]"

def get_db_connection():
    db_url = get_database_url()
    if not db_url:
        raise HTTPException(status_code=500, detail="Database URL não configurada")
    return psycopg2.connect(db_url, sslmode='require')

@router.get("/cases")
async def list_active_cases():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, clinical_history, primary_diagnosis, 
                   patient_demographics, taxonomies, media_urls, svg_json, created_at, updated_at
            FROM clinical_cases WHERE is_deleted = FALSE ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        def safe_json(val, default):
            if isinstance(val, (dict, list)): return val
            if not val: return default
            try: return json.loads(val)
            except: return default

        cases = []
        for r in rows:
            cases.append({
                "id": r[0],
                "title": r[1],
                "clinical_history": r[2],
                "primary_diagnosis": r[3],
                "patient_demographics": safe_json(r[4], {}),
                "taxonomies": safe_json(r[5], []),
                "media_urls": safe_json(r[6], []),
                "svg_json": r[7],
                "created_at": r[8],
                "updated_at": r[9]
            })
        return {"success": True, "cases": cases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cases")
async def create_case(case: ClinicalCasePayload, _admin: str = Depends(verify_admin)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            INSERT INTO clinical_cases 
            (title, clinical_history, primary_diagnosis, patient_demographics, taxonomies, media_urls, svg_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        cur.execute(query, (
            case.title, 
            case.clinical_history, 
            case.primary_diagnosis, 
            json.dumps(case.patient_demographics),
            json.dumps(case.taxonomies),
            json.dumps(case.media_urls),
            case.svg_json
        ))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True, "id": new_id, "message": "Caso criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cases/rescue-count")
async def get_rescue_count():
    """Conta casos 'Resgate Nuvem' no Acervo aguardando curadoria."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM clinical_cases
            WHERE title LIKE 'Resgate Nuvem:%%'
            AND is_deleted = FALSE
        """)
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cases/training-export")
async def training_export():
    """
    Exporta todos os casos marcados como 'retrain_candidate' para alimentar o pipeline de retreino.
    Retorna { id, correct_class, image_url } — prontos para o data_sync.py ou script de dataset.
    Apenas leitura — nunca modifica dados.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, primary_diagnosis, media_urls, taxonomies
            FROM clinical_cases
            WHERE is_deleted = FALSE
              AND taxonomies::text LIKE '%%retrain_candidate%%'
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        def safe_json(val, default):
            if isinstance(val, (dict, list)): return val
            if not val: return default
            try: return json.loads(val)
            except: return default

        export = []
        for r in rows:
            case_id, primary_diagnosis, media_urls_raw, taxonomies_raw = r
            urls = safe_json(media_urls_raw, [])
            taxonomies = safe_json(taxonomies_raw, [])
            if urls:
                export.append({
                    "id": case_id,
                    "correct_class": primary_diagnosis or "sem_diagnostico",
                    "image_url": urls[0],
                    "all_taxonomies": taxonomies,
                })

        return {"success": True, "total": len(export), "cases": export}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cases/{case_id}")
async def get_case(case_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, clinical_history, primary_diagnosis, 
                   patient_demographics, taxonomies, media_urls, svg_json, created_at, updated_at
            FROM clinical_cases WHERE id = %s AND is_deleted = FALSE
        """, (case_id,))
        r = cur.fetchone()
        cur.close()
        conn.close()
        
        if not r:
            raise HTTPException(status_code=404, detail="Caso não encontrado")
            
        def safe_json(val, default):
            if isinstance(val, (dict, list)): return val
            if not val: return default
            try: return json.loads(val)
            except: return default
            
        case = {
            "id": r[0], "title": r[1], "clinical_history": r[2], "primary_diagnosis": r[3],
            "patient_demographics": safe_json(r[4], {}), "taxonomies": safe_json(r[5], []), "media_urls": safe_json(r[6], []), 
            "svg_json": r[7], "created_at": r[8], "updated_at": r[9]
        }
        return {"success": True, "case": case}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/cases/{case_id}")
async def update_case(case_id: int, case: ClinicalCasePayload, _admin: str = Depends(verify_admin)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            UPDATE clinical_cases 
            SET title = %s, clinical_history = %s, primary_diagnosis = %s, 
                patient_demographics = %s, taxonomies = %s, media_urls = %s, 
                svg_json = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND is_deleted = FALSE
        """
        cur.execute(query, (
            case.title, case.clinical_history, case.primary_diagnosis, 
            json.dumps(case.patient_demographics), json.dumps(case.taxonomies), 
            json.dumps(case.media_urls), case.svg_json, case_id
        ))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Caso não encontrado")
            
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True, "message": "Caso atualizado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SVGPayload(BaseModel):
    svg_json: str

@router.patch("/cases/{case_id}/svg")
async def update_svg(case_id: int, payload: SVGPayload, _admin: str = Depends(verify_admin)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = "UPDATE clinical_cases SET svg_json = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s AND is_deleted = FALSE"
        cur.execute(query, (payload.svg_json, case_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Caso não encontrado")
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True, "message": "SVG salvo na V4 com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cases/rescue-to-curadoria")
async def rescue_to_curadoria(_admin: str = Depends(verify_admin)):
    """
    Move todos os casos 'Resgate Nuvem' do Acervo para a fila InboxML (tabela feedback).
    Insere na tabela feedback e faz soft-delete na clinical_cases.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, title, media_urls FROM clinical_cases
            WHERE title LIKE 'Resgate Nuvem:%%'
            AND is_deleted = FALSE
        """)
        rows = cur.fetchall()

        if not rows:
            cur.close()
            conn.close()
            return {"success": True, "migrated": 0, "message": "Nenhum caso Resgate Nuvem encontrado no Acervo."}

        migrated = 0
        skipped = 0

        for row in rows:
            case_id, title, media_urls_raw = row

            try:
                if isinstance(media_urls_raw, list):
                    urls = media_urls_raw
                elif media_urls_raw:
                    urls = json.loads(media_urls_raw)
                else:
                    urls = []
            except Exception:
                urls = []

            image_url = urls[0] if urls else None

            if not image_url:
                skipped += 1
                continue

            cur.execute("""
                INSERT INTO feedback
                    (feedback_image_url, correct_diagnosis, diagnosis_correct, predicted_classes, clinical_case)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                image_url,
                'SEM DIAGNÓSTICO',
                False,
                json.dumps(''),
                title,
            ))

            cur.execute(
                "UPDATE clinical_cases SET is_deleted = TRUE WHERE id = %s",
                (case_id,)
            )
            migrated += 1

        conn.commit()
        cur.close()
        conn.close()

        msg = f"{migrated} casos Resgate Nuvem enviados para a fila de curadoria (InboxML)."
        if skipped:
            msg += f" {skipped} caso(s) ignorado(s) por ausência de URL de imagem."

        return {"success": True, "migrated": migrated, "skipped": skipped, "message": msg}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/cases/{case_id}")
async def delete_case(case_id: int, _admin: str = Depends(verify_admin)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE clinical_cases SET is_deleted = TRUE WHERE id = %s", (case_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Caso não encontrado")
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True, "message": "Caso deletado (Soft Delete)"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_media(file: UploadFile = File(...), _admin: str = Depends(verify_admin)):
    if not setup_cloudinary():
        raise HTTPException(status_code=500, detail="Cloudinary não configurado")
    try:
        contents = await file.read()
        secure_url = upload_to_cloudinary_rest(contents, "otoscopia_atlas_gen4")
        if not secure_url:
            raise HTTPException(status_code=500, detail="Falha ao obter URL do Cloudinary")
        return {"success": True, "url": secure_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
