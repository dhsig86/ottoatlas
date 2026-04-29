import requests
import json

url = "https://otto-atlas.onrender.com/api/predict"
image_path = r"C:\Users\drdhs\OneDrive\Imagens\Otoscopio 2026\IMG\IMG00001.jpg"

try:
    print(f"Testando POST para: {url}...")
    with open(image_path, "rb") as img_file:
        files = {"file": img_file}
        response = requests.post(url, files=files, timeout=60)
        
    print(f"Status HTTP: {response.status_code}")
    print(f"Resposta bruta: {response.text}")
    print("Sucesso! Diagnóstico alcançado!" if response.status_code == 200 else "Falha no servidor traseiro.")
    
except Exception as e:
    print(f"Erro ao testar a API remota: {e}")
