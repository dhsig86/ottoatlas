import cloudinary
import cloudinary.api
import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv('.env')
c_url = os.environ.get('CLOUDINARY_URL').replace('cloudinary://', '')
api_key, rest = c_url.split(':', 1)
api_secret, cloud_name = rest.split('@', 1)
cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

db_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db_url, sslmode='require')
cur = conn.cursor()

def rescue_folder(folder_name):
    print(f"Resgatando fotos da pasta {folder_name}...")
    res = cloudinary.api.resources(type='upload', prefix=folder_name, max_results=500)
    items = res.get('resources', [])
    print(f"Encontrados {len(items)} arquivos em {folder_name}")
    
    count = 0
    for file in items:
        url = file['secure_url']
        public_id = file['public_id'].split('/')[-1]
        
        # Check if already exists
        cur.execute("SELECT id FROM clinical_cases WHERE media_urls::text LIKE %s", ('%' + url + '%',))
        if cur.fetchone():
            continue
            
        cur.execute("""
            INSERT INTO clinical_cases 
            (title, clinical_history, primary_diagnosis, taxonomies, media_urls, svg_json)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            f"Resgate Nuvem: {public_id}",
            "Caso recuperado da hospedagem nativa.",
            "Sem Diagnóstico (Resgate)",
            json.dumps(["pure_ml"]),
            json.dumps([url]),
            "[]"
        ))
        conn.commit()
        count += 1
    print(f"{count} inseridos na base V4 com sucesso.")

if __name__ == '__main__':
    rescue_folder('curadoria_gen4')
    rescue_folder('otoscopia_atlas_nuvem')
    rescue_folder('otoscopia_colaboracao_externa')
    cur.close()
    conn.close()
    print("Resgate finalizado.")
