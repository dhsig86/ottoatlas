import os

dirs_to_check = [
    r"C:\Users\drdhs\OneDrive\Documentos\ottoatlas\OTTO_ML_Dataset",
    r"C:\Users\drdhs\OneDrive\Documentos\APPROTTO\PORTFOLIO_OFICIAL_ML",
    r"C:\Users\drdhs\OneDrive\Imagens\Otoscopio 2026\IMG"
]

print("=== RELATORIO DE AUDITORIA DO DATASET ===")
with open('dataset_report.txt', 'w') as f:
    for d in dirs_to_check:
        f.write(f"\n--- Analisando: {d} ---\n")
        if not os.path.exists(d):
            f.write(">> DIRETORIO NAO ENCONTRADO!\n")
            continue
        
        total_files = 0
        for root, dirs, files in os.walk(d):
            img_files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if img_files:
                rel_path = os.path.relpath(root, d)
                if rel_path == ".": rel_path = "RAIZ"
                f.write(f"[{rel_path}] -> {len(img_files)} imagens\n")
                total_files += len(img_files)
        f.write(f"Total na pasta principal: {total_files} imagens\n")
