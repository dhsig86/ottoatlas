# OTTO Frame Extractor (Módulo de Aquisição MLOps)

Este é um módulo isolado e nativo em Python para extração massiva de fotos (frames) a partir de vídeos clínicos brutos de otoscopia.
Seu objetivo é pulverizar vídeos longos em dezenas de frames cruciais para treinar a Inteligência Artificial (Fast.ai / PyTorch), filtrando logicamente usando a matemática da Variância Laplaciana as imagens que estão embaçadas/desfocadas.

---

## 🛠️ Requisitos de Instalação (VS Code)
1. Certifique-se de que o Python 3.10+ está instalado.
2. Abra o terminal do VS Code (`Ctrl + '`) e navegue até esta nova pasta:
   ```cmd
   cd C:\Users\drdhs\OneDrive\Documentos\ottoatlas\frame_extractor
   ```
3. (Opcional mas recomendado) Crie um ambiente virtual Python para este módulo isolado:
   ```cmd
   python -m venv venv
   .\venv\Scripts\activate
   ```
4. Instale as bibliotecas matemáticas pesadas de visão computacional (OpenCV):
   ```cmd
   pip install -r requirements.txt
   ```

---

## 🚀 Como Usar e Executar

Primeiro, você deve colocar seus vídeos de otóscopio (ex: `Paciente_Carlos.mp4`, `Exame_Otite.mp4`) dentro de uma pasta, por exemplo, criando uma pasta chamada `meus_videos` aqui mesmo dentro.

**Comando Básico no Terminal:**
```cmd
python main.py --input meus_videos --output frames_prontos
```

### Exemplo Real e Completo (Mais poderoso)
Neste pipeline, vamos extrair uma foto a cada `0.5` segundos de vídeo, descartando todas as fótos que tenham nitidez abaixo de `80` na métrica de foco, e criaremos um arquivo Relatório MLOps de Diagnóstico (`.csv`).

**Comando:**
```cmd
python main.py --input meus_videos --output meus_frames_filtrados --interval 0.5 --sharpness-threshold 80 --csv
```

### Explicação dos Parâmetros

| Argumento | Definição | Exemplo Válido |
| :--- | :--- | :--- |
| `--input` | **(Obrigatório)** Pasta onde estão os arquivos `.mp4` ou `.avi` originais. | `--input videos` |
| `--output` | **(Obrigatório)** Pasta onde as fotos serão salvas. | `--output extraidos` |
| `--interval`| Define o delta de tempo (segundos). | `--interval 1.0` (Estrai 1 frame por segundo) |
| `--sharpness-threshold` | Mínimo aceitável do filtro de Laplaciano. Se a foto for um borrão e bater 40, ela é deletada. | `--sharpness-threshold 100.0` |
| `--csv` | Uma tag de gatilho (`flag`). Se digitada, pede a criação de base em Excel. | `--csv` |

---
**Desenvolvido para:** Ecossistema OTTO (Captação Dinâmica Local e Deploy Render).
