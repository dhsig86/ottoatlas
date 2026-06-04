"""
Motor de Treinamento Contínuo: OTTO Atlas AI Diagnóstico
--------------------------------------------------------
Transfer Learning com ResNet18 via Fast.ai (PyTorch).

PIPELINE:
  1. Carrega dataset de OTTO_ML_Dataset/ (splits TRAIN/VALIDATION/TEST)
  2. Aplica online augmentation clinicamente segura
  3. Fine-tune com EarlyStopping + SaveModelCallback
  4. Exporta modelo .pkl e vocab.txt
  5. Gera metricas de avaliacao (confusion matrix, per-class accuracy)

NOTA CLÍNICA: O diretório de dataset serve apenas como "Leitura" (Read-Only).
Nada é apagado ou modificado nos dados originais do Dr. Dario.

Autor: Pipeline MLOps OTTO Atlas
Atualizado: 2026-06-04
"""

from fastai.vision.all import *
from pathlib import Path
import warnings
import sys
import json
from datetime import datetime

# Ignorar alertas verbosos para um console limpo
warnings.filterwarnings('ignore')


def train_otto_model(samples_dir, output_dir, epochs=15):
    path = Path(samples_dir)
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True, parents=True)
    
    print("=" * 65)
    print("OTOSCOP-IA — Motor de Treinamento v2.0")
    print("=" * 65)
    print(f"Dataset:  {path}")
    print(f"Output:   {out_path}")
    print(f"Epochs:   {epochs}")
    print(f"Inicio:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar se o dataset existe e tem splits
    train_dir = path / 'TRAIN'
    valid_dir = path / 'VALIDATION'
    
    if not train_dir.exists():
        print(f"[ERRO] Pasta TRAIN nao encontrada em {path}")
        sys.exit(1)
    if not valid_dir.exists():
        print(f"[ERRO] Pasta VALIDATION nao encontrada em {path}")
        sys.exit(1)
    
    # Contar classes e amostras
    train_classes = [d.name for d in train_dir.iterdir() if d.is_dir()]
    print(f"[INFO] Classes detectadas ({len(train_classes)}): {', '.join(sorted(train_classes))}")
    for cls_dir in sorted(train_dir.iterdir()):
        if cls_dir.is_dir():
            n_train = len(list(cls_dir.glob('*.*')))
            n_val_dir = valid_dir / cls_dir.name
            n_val = len(list(n_val_dir.glob('*.*'))) if n_val_dir.exists() else 0
            print(f"  {cls_dir.name:<25s}: TRAIN={n_train:>4d}  VAL={n_val:>4d}")
    print()
    
    # ================================================================
    # DATA AUGMENTATION CLINICO (Online — aplicado a cada epoch)
    # ================================================================
    # Otoscopio roda 360° no canal, brilho varia com angulo de luz,
    # orelha E/D sao espelhadas. Transforms preservam landmarks.
    # ================================================================
    
    print("[INFO] Configurando DataLoaders com augmentation clinica...")
    
    dls = ImageDataLoaders.from_folder(
        path,
        train='TRAIN',
        valid='VALIDATION',
        item_tfms=Resize(256),  # Pre-resize (256 -> crop 224). Cabe na GTX 1650 4GB
        batch_tfms=aug_transforms(
            size=224,              # Tamanho final do input ResNet
            min_scale=0.80,        # Zoom: 80-100% (simula distancia do otoscopio)
            max_rotate=360.0,      # Rotacao livre (otoscopio gira no canal)
            max_lighting=0.25,     # Brilho/contraste ±25%
            max_zoom=1.15,         # Zoom in leve
            max_warp=0.0,          # SEM warp (destruiria landmarks clinicos)
            p_affine=0.80,         # 80% de chance de aplicar transforms geometricos
            p_lighting=0.75,       # 75% de chance de variar iluminacao
            do_flip=True,          # Flip horizontal (orelha E↔D)
            flip_vert=True,        # Flip vertical
        ),
        num_workers=0,  # CRITICO: evita freeze no Windows
        bs=8             # Batch size seguro para GTX 1650 (4GB VRAM)
    )
    
    print(f"[INFO] Vocabulario do modelo: {dls.vocab}")
    print(f"[INFO] TRAIN batches: {len(dls.train)}, VAL batches: {len(dls.valid)}")
    print()
    
    # ================================================================
    # MODELO: ResNet18 com Transfer Learning
    # ================================================================
    # ResNet18: leve (11M params), rapido, otimo para deploy mobile/ONNX.
    # Fine-tune: congela camadas base, treina apenas o classificador.
    # ================================================================
    
    print("[INFO] Carregando ResNet18 pre-treinado (ImageNet)...")
    learn = vision_learner(dls, resnet18, metrics=[error_rate, accuracy])
    
    # ================================================================
    # TREINAMENTO com Guardioes contra Overfitting
    # ================================================================
    
    print(f"[INFO] Iniciando fine-tune ({epochs} epochs max)...")
    print()
    
    cbs = [
        # Para se a validation loss parar de melhorar por 4 epochs
        EarlyStoppingCallback(monitor='valid_loss', min_delta=0.005, patience=4),
        # Salva o modelo da melhor epoch (menor error_rate)
        SaveModelCallback(monitor='error_rate', fname='best_model', min_delta=0.005),
    ]
    
    learn.fine_tune(epochs, cbs=cbs)
    
    print()
    print("=" * 65)
    print("[INFO] Treinamento finalizado. Gerando metricas...")
    print("=" * 65)
    print()
    
    # ================================================================
    # AVALIACAO: Per-class metrics
    # ================================================================
    
    try:
        # Confusion matrix
        interp = ClassificationInterpretation.from_learner(learn)
        cm = interp.confusion_matrix()
        
        print("CONFUSION MATRIX:")
        print(f"{'':>25s}", end="")
        for v in dls.vocab:
            print(f"{v[:8]:>10s}", end="")
        print()
        
        for i, row in enumerate(cm):
            print(f"  {dls.vocab[i]:<23s}", end="")
            for val in row:
                print(f"{val:>10d}", end="")
            print()
        print()
        
        # Per-class accuracy
        print("PER-CLASS ACCURACY:")
        for i, cls_name in enumerate(dls.vocab):
            tp = cm[i][i]
            total = cm[i].sum()
            acc = tp / total * 100 if total > 0 else 0
            bar = "#" * int(acc / 2)
            print(f"  {cls_name:<25s} {acc:>5.1f}% ({tp}/{total})  {bar}")
        
        # Overall accuracy
        total_correct = sum(cm[i][i] for i in range(len(dls.vocab)))
        total_samples = cm.sum()
        overall_acc = total_correct / total_samples * 100 if total_samples > 0 else 0
        print(f"\n  {'OVERALL':<25s} {overall_acc:>5.1f}% ({total_correct}/{total_samples})")
        
    except Exception as e:
        print(f"[WARN] Nao foi possivel gerar metricas detalhadas: {e}")
    
    # ================================================================
    # EXPORTACAO
    # ================================================================
    
    print()
    print("=" * 65)
    print("[INFO] Exportando modelo...")
    print("=" * 65)
    
    # 1. Exportar .pkl (FastAI)
    export_file = out_path / 'otto_diagnostic_model.pkl'
    learn.export(export_file)
    print(f"  [OK] Modelo FastAI: {export_file}")
    
    # 2. Atualizar vocab.txt (para ONNX runtime)
    vocab_file = out_path / 'vocab.txt'
    with open(vocab_file, 'w', encoding='utf-8') as f:
        for cls_name in dls.vocab:
            f.write(f"{cls_name}\n")
    print(f"  [OK] Vocabulario: {vocab_file}")
    print(f"       Classes: {list(dls.vocab)}")
    
    # 3. Salvar metadata do treino
    metadata = {
        "trained_at": datetime.now().isoformat(),
        "epochs_requested": epochs,
        "architecture": "resnet18",
        "classes": list(dls.vocab),
        "n_classes": len(dls.vocab),
        "train_samples": len(dls.train.dataset),
        "valid_samples": len(dls.valid.dataset),
        "augmentation": {
            "online": "aug_transforms(max_rotate=360, max_lighting=0.25, max_zoom=1.15, no_warp)",
            "offline": "minority_balanced_to_80_per_class"
        },
    }
    
    metadata_file = out_path / 'training_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Metadata: {metadata_file}")
    
    print()
    print(f"  [!] PROXIMO: Rode export_onnx.py para converter .pkl -> .onnx")
    print(f"  [!] Deploy: Copie otto_model.onnx + vocab.txt para /var/data no Render")
    
    return learn


if __name__ == '__main__':
    # Paths atualizados para o ecossistema AOTTO
    SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SCRIPT_DIR.parent.parent  # ottoatlas/
    
    DATASET_DIR = PROJECT_ROOT / "OTTO_ML_Dataset"
    OUTPUT_DIR = SCRIPT_DIR / "models"
    
    try:
        learn = train_otto_model(str(DATASET_DIR), str(OUTPUT_DIR), epochs=15)
    except Exception as e:
        print(f"\n[ERRO CRITICO] {e}")
        import traceback
        traceback.print_exc()
        print("\nCertifique-se de instalar: pip install fastai torch torchvision")
