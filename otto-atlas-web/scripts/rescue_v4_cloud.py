import cloudinary
import cloudinary.api
import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv()
c_url = os.environ.get('CLOUDINARY_URL').replace('cloudinary://', '')
api_key, rest = c_url.split(':', 1)
api_secret, cloud_name = rest.split('@', 1)
cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

db_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db_url, sslmode='require')
cur = conn.cursor()

def run_rescue():
    print("Conectando ao Cloudinary para resgatar atlas_cases_gen4...")
    try:
        res = cloudinary.api.resources(type='upload', prefix='atlas_cases_gen4', max_results=500)
        items = res.get('resources', [])
        print(f"Encontradas {len(items)} fotos no Cloudinary.")
        
        count = 0
        for file in items:
            url = file['secure_url']
            public_id = file['public_id'].split('/')[-1]
            
            # Check if it already exists
            cur.execute("SELECT id FROM clinical_cases WHERE media_urls::text LIKE %s", ('%' + url + '%',))
            if cur.fetchone():
                continue
            
            # Identify if it was from quiz or just generic
            taxonomies = []
            if "quiz" in public_id.lower() or "pergunta" in public_id.lower():
                taxonomies = ["quiz_only"]
                
            cur.execute("""
                INSERT INTO clinical_cases 
                (title, clinical_history, primary_diagnosis, taxonomies, media_urls, svg_json)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"Resgate Nuvem: {public_id}",
                "Caso recuperado automaticamente da nuvem Cloudinary.",
                "Sem Diagnóstico",
                json.dumps(taxonomies),
                json.dumps([url]),
                "[]"
            ))
            conn.commit()
            count += 1
            
        print(f"{count} NOVOS casos foram restaurados com sucesso para o banco V4.")
    except Exception as e:
        print("Erro Crítico:", e)

if __name__ == '__main__':
    run_rescue()
    cur.close()
    conn.close()
