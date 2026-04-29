import requests
import sys

def wipe_all_cases():
    api_base = "https://ottos-v4-fastapi.onrender.com"
    try:
        print("Buscando todos os casos no servidor V4...")
        response = requests.get(f"{api_base}/api/cms/cases")
        data = response.json()
        
        if not data.get("success") or not data.get("cases"):
            print("Nenhum caso encontrado ou erro na API.")
            return

        cases = data["cases"]
        print(f"Foram encontrados {len(cases)} casos. Iniciando o extermínio cirúrgico...")

        deleted_count = 0
        for c in cases:
            case_id = c["id"]
            title = c.get("title", f"Caso {case_id}")
            del_resp = requests.delete(f"{api_base}/api/cms/cases/{case_id}")
            if del_resp.status_code == 200:
                print(f"✅ Apagado: {title} (ID {case_id})")
                deleted_count += 1
            else:
                print(f"❌ Falha ao apagar (ID {case_id}): {del_resp.text}")

        print(f"\nWipe Concluído: {deleted_count} casos destruídos. O V4 está completamente limpo.")

    except Exception as e:
        print(f"Erro Crítico durante o Wipe: {e}")

if __name__ == "__main__":
    if input("Isso vai apagar TUDO da Nuvem V4. Digite 'sim' para continuar: ") == 'sim':
        wipe_all_cases()
    else:
        print("Abortado.")
