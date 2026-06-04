# Relatório de Viabilidade Científica e Técnica: Mapeamento de Estruturas Anatômicas (Sumotosima Framework) no OTTO Atlas
**Autor:** Antigravity (IA Assistente de Otorrinolaringologia Digital)  
**Data:** 4 de Junho de 2026  
**Status:** Proposta de Projeto para OTTO Atlas Gen 5.0  

---

## 1. Resumo Executivo
Este documento apresenta uma análise de viabilidade técnica, arquitetura de pipeline e mapeamento de dataset para a evolução do **OTOSCOP-IA** de um classificador puro (Gen 4.0) para um **sistema híbrido de segmentação anatômica e textualização/geração de laudos estruturados** (Gen 5.0). 

Inspirado no modelo **Sumotosima** (*Summarizer for Otoscopic Images*), o objetivo é fazer com que o OTTO Atlas não apenas rotule a patologia global da orelha (ex: OMA, Otomicose), mas sim identifique, delimite poligonalmente e gere um sumário clínico das principais estruturas anatômicas da membrana timpânica (MT) e conduto auditivo externo (CAE).

---

## 2. O Conceito: Identificação e Detalhamento Estrutural
Diferente da classificação estática clássica (que avalia a imagem como um todo), a evolução proposta atua em duas frentes complementares:

1. **Reconhecimento Geométrico de Estruturas (Visão):** Delimitar a localização exata das estruturas normais e patológicas sobre a imagem do tímpano:
   * **Cabo do Martelo (Malleus Handle)**
   * **Processo Curto do Martelo (Lateral Process)**
   * **Triângulo Luminoso (Cone of Light / Reflexo Luminoso)**
   * **Umbigo do Tímpano (Umbo)**
   * **Pars Flaccida** (Shrapnell's membrane)
   * **Pars Tensa**
   * **Bigorna (Incus)** (visível por transparência em tímpanos normais/finos)
   * **Perfurações / Bolsas de Retração** (se presentes)

2. **Textualização Clínica (Sumarização/Geração de Laudo):** Com base nas estruturas identificadas e suas características (cor, brilho, integridade, posição), gerar um resumo legível e estruturado focado no paciente ou no residente médico (HITL).

---

## 3. Estruturação do Dataset Necessário
A maior barreira para a implantação do framework Sumotosima na prática clínica é a escassez de datasets contendo anotações a nível de objeto (polígonos/hotspots) e descrições textuais ricas em português.

Para treinar o modelo Gen 5.0, o dataset precisa ser estruturado no seguinte formato:

```
[Imagem Otoscópica] ──► [Anotações de Segmentação (COCO JSON)] ──► [Descrição Clínica Textual]
```

### A. Especificação das Classes de Segmentação (Polígonos/Boxes)
Para o motor de visão (ex: YOLOv8-seg, Mask R-CNN ou SAM-fine-tuned), cada imagem no dataset deve possuir polígonos de contorno para:
* `cabo_martelo`: Polígono linear acompanhando a extensão do martelo.
* `processo_curto`: Pequena elipse na porção superior do cabo.
* `triangulo_luminoso`: Polígono triangular ou irregular na região anteroinferior.
* `umbo`: Círculo de precisão no centro da MT (final do cabo).
* `pars_flaccida`: Área elíptica superior (acima do processo curto).
* `pars_tensa`: Grande área inferior da MT.
* `perfuracao`: Contorno exato do defeito timpânico, se houver.
* `bolsa_retracao`: Contorno da área de invaginação da membrana, se houver.

### B. Especificação dos Pares Imagem-Texto (para Geração de Laudo)
Para o gerador textual (ex: LLM fine-tuned ou modelo BART Multimodal como no Sumotosima original), cada imagem precisa estar vinculada a um laudo normalizado em português:
* *Exemplo de Label Textual:* "Membrana timpânica íntegra, de coloração translúcida cinza-pérola. Cabo do martelo e processo curto bem delineados e em posição neutra. Triângulo luminoso presente e posicionado no quadrante anteroinferior. Sem sinais de efusão ou perfurações."

---

## 4. Análise de Dificuldade de Implantação
A implantação do Sumotosima Framework no ecossistema OTTO apresenta complexidades distintas divididas em três eixos:

### 4.1. Complexidade de ML e Treinamento (Alta Dificuldade)
* **Anotação de Dados (Gargalo Principal):** Rotular manualmente polígonos sobre centenas de otoscopias exige tempo clínico especializado do Dr. Dario e assistentes. 
* **Conversão do Mapeamento SVG:** Hoje, o OTTO Atlas já possui o **Estúdio SVG** (SVGStudio.tsx), onde o médico desenha hotspots. Podemos exportar esse banco (`svg_json` no Postgres) para gerar o dataset de segmentação no formato COCO de forma automática! Isso reduz a dificuldade de anotação de "Extrema" para "Moderada".
* **Inferência de Modelos Multimodais:** Modelos como BART Multimodal combinam pesos de imagem (Vision Transformer) e texto (BART). Eles são pesados e não rodam bem em CPU com 512MB de RAM (Render Free Tier).

### 4.2. Complexidade de Integração no Backend (Média Dificuldade)
* **Arquitetura de Dois Motores:** Em vez de rodar um modelo multimodal pesado diretamente, a forma mais eficiente de implementar no OTTO Atlas é criar uma cascata leve:
  1. **Motor de Segmentação (ONNX):** Um modelo YOLOv8-seg exportado para ONNX (cerca de 15MB) que roda rapidamente na CPU do Render e retorna as coordenadas dos polígonos anatômicos.
  2. **Motor de Geração Textual (API/RAG):** Em vez de rodar um modelo de linguagem no Render, enviamos as classes detectadas e suas coordenadas para o pipeline GPT-4o-mini (via RAG no backend FastAPI) para estruturar o laudo/resumo.

### 4.3. Complexidade no Frontend (Baixa Dificuldade)
* O OTTO Atlas já possui suporte a renderização de SVG interativo sobre imagens. A exibição de bounding-boxes ou polígonos sobrepostos na tela do médico residentes exigirá apenas o mapeamento do output JSON do ONNX para elementos `<path>` em SVG, algo que o modulo [SVGStudio.tsx](file:///C:/Users/drdhs/OneDrive/Documentos/AOTTO%20ECOSYSTEM/ottoatlas/otto-atlas-web/src/components/SVGStudio.tsx) já executa nativamente.

---

## 5. Arquitetura Proposta para o OTTO Atlas Gen 5.0

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React/Vite)                  │
│  - Captura da imagem + compressão (imageCompressor.ts)      │
│  - Envio da requisição de imagem ao Render                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI/ONNX)                  │
│                                                             │
│  1. Motor de Visão (YOLOv8-seg em ONNX - CPU Runtime)       │
│     - Executa segmentação de instâncias                     │
│     - Retorna: [ { classe: cabo_martelo, poligono: [...] } ] │
│                                                             │
│  2. NLP / RAG Pipeline (GPT-4o-mini / Claude 3.5 Haiku)      │
│     - Recebe as coordenadas e classes anatômicas            │
│     - Constrói o Prompt clínico com base em diretrizes      │
│     - Gera laudo estruturado e resumo em Português          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Visualização de Resultados                   │
│  - Desenho automático dos SVGs anatômicos sobre a imagem    │
│  - Exibição de laudo explicativo (detalhado e simplificado) │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Veredicto e Plano de Ação Recomendado

> [!TIP]
> **Recomendação de Viabilidade:**
> A implantação de uma arquitetura baseada no Sumotosima Framework é **altamente viável**, desde que seja adotado o modelo híbrido **(YOLOv8-seg ONNX + GPT-4o API)**, em vez de um modelo multimodal customizado monolítico, contornando a limitação de hardware do Render.

### Próximos Passos Clínicos e Técnicos:
1. **Aproveitamento do SVG Studio:** Continuar utilizando o [SVGStudio.tsx](file:///C:/Users/drdhs/OneDrive/Documentos/AOTTO%20ECOSYSTEM/ottoatlas/otto-atlas-web/src/components/SVGStudio.tsx) para mapear anatomicamente as imagens do acervo do Atlas. Cada marcação gerada cria um ponto de treino para o futuro segmentador.
2. **Script de Extração COCO:** Desenvolver um script Python (`export_svg_to_coco.py`) para ler a tabela `clinical_cases` (campo `svg_json`) e gerar automaticamente as máscaras de treino em formato YOLO/COCO.
3. **Treinamento de Modelo YOLOv8-seg:** Uma vez atingido o limiar de 150 a 200 imagens com marcações anatômicas ricas no banco Postgres, realizar o fine-tuning de um modelo de segmentação ultraleve (YOLOv8n-seg) e exportá-lo para ONNX.
