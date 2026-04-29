# Relatório Executivo do Status da Aplicação — OTTO Atlas (V4.1)

> [!IMPORTANT]
> Este documento analisa exaustivamente o esqueleto técnico atual do OTTO Atlas. A aplicação encontra-se na versão **V4.1**, onde consolidou sua arquitetura *Edge-to-Cloud* de forma assíncrona, curando as limitações históricas de *Out-Of-Memory* e latência.

---

## 1. Topografia e Infraestrutura (DevOps)

A infraestrutura foi segmentada para garantir estabilidade operacional isolando completamente o ciclo de requisição web (rápido) do ciclo preditivo neural (pesado).

*   **Frontend Web (Vercel):** Aplicação despachada via Vercel. Todo o código *Python/FastAPI* (pasta `ml_pipeline/`) é ignorado na compilação do front via `.vercelignore`, impedindo gargalos de build.
*   **Backend Preditivo (Render.com):** Motor FastAPI operado no Render (PaaS). A solução magna para contenção de custos (evitando super-servidores de GPU) foi a adesão a Discos Persistentes (`/var/data`). O arquivo pesadíssimo do motor neural (`otto_model.onnx` de ~83MB) não transita mais em repasses git; ele "mora" fixo no disco seguro do Render.
*   **Media Delivery (Cloudinary):** Transição integral completada. Subiu-se o patamar de arquivos rasos para uma API *Cloudinary* nativa. Hospeda as imagens com eficiência transacional em pastas específicas (`otoscopia_atlas_nuvem`, `curadoria_gen4`, etc).
*   **Datastore Racional (Neon Tech):** Banco de Dados PostgreSQL *Serverless* provendo os esquemas cruciais: `atlas_cloud_items` (o Atlas em si), `clinical_cases` (laudos fechados/quiz) e `feedback` (a fila imunda da Curadoria). Suporta armazenamento passivo de vetores poligonais nativos usando JSON e campos textuais longos.

---

## 2. Frontend Clínico (Camada de Apresentação)

Desenvolvido inteiramente na fundação moderna do **React 18 + Vite**, o ambiente é blindado por chaves rígidas de tipagem do **TypeScript** (garantia cirúrgica de predição do compilação) e adoção de injeções estéticas utilitárias com **TailwindCSS** e iconografia **Lucide React**.

**Principais Módulos Consolidados (`src/components`):**
*   **`AIAnalyzer.tsx`**: Interface mestre de ingestão. Permite anexação de imagens, lida com as invocações de predição e mostra o progresso do diagnóstico da máquina.
*   **`AtlasManagerV4.tsx` & `AtlasGrid.tsx`**: O hub controlador de dados em núvem (*Cloud CMS*), listando dinamicamente (*lazy load*) os casos processados a partir das consultas via FastAPI / NeonDB.
*   **Laboratório de Visão Espacial (`SVGStudio.tsx` & `ImageDetailModal.tsx`)**: Uma suíte pesada desenhada em Canvas HTML5. Permite aos curadores plotar *Hotspots*/Polígonos (*Bounding Boxes*) vetoriais perfeitos sobre áreas anatômicas (como delinear um colesteatoma destrutivo).
*   **`CurationHubV4.tsx` & `MLCuradoria.tsx`**: Painéis da usina geradora de *dataset*. Renderiza tudo o que está entupindo a fila de `pendentes` e permite a interface *Human-in-the-Loop* varrer falsos-positivos/negativos.
*   **Extensões Sociais e Práticas:** Suporte ao engajamento com o módulo de submissões espontâneas `CommunityDonation.tsx` e `OtoscopyInstructionsModal.tsx` como manual de manobras de ponta.

---

## 3. Backend e Motor Neural AI (FastAPI / ONNX)

O "cérebro" contido em `ml_pipeline/main.py` foi reprogramado seguindo dogmas rigorosos de alocação de memória enxuta e ingestão REST.

### 3.1. A Conversão para Matemática Leve (ONNXRuntime)
Em vez de depender das toneladas de extensões do `PyTorch`, a aplicação invoca a inteligência em C++ nativa e crua pelo **ONNX** via `CPUExecutionProvider`.
A inteligência possui *Lazy Loading*: se a rota de predição primária nunca for ativada no dia, ela não rouba a RAM. Quando ativada, lê o `otto_model.onnx` e o `vocab.txt` do disco, retendo meros ~350MB, mitiganso completamente *Timeouts* aleatórios e pânicos de *Out-Of-Memory*.

### 3.2. Fluxo da IA (Rota `/api/predict`)
1.  **Recepção:** Aceita imagens fotográficas gigantes da requisição pura do edge.
2.  **Transmutação (NumPy/PIL):** Converte a mídia para tensores de tamanho (3, 224, 224) RGB cravados. Executa normalização *ImageNet* rígida com desvios padrões matemáticos (a aplicação PyTorch exige os canais no eixo `img_arr = np.transpose`).
3.  **Acurácia Dinâmica (Softmax):** Emana o logaritmo resultante em distribuições probabilísticas fidedignas e em formatação limpa (ex: `Otite Media Serosa` a 99% será mapeada via vocabulário fixo). 

### 3.3. Rotas Administrativas e Curadoria (A Esteira de MLOps)
*   **API Preditiva de Base (`/api/feedback`)**: Aceita as consultas dos médicos da Atenção Básica, hospeda pro Cloudinary e loga a requisição e a decisão no Postgress table `feedback`.
*   **Tratagem da Curadoria (`/api/curadoria/approve`)**: Se o Curador ratifica a assertividade da IA, ela "desce" de `feedback`, vai direto para Ouro Sagrado preenchendo a tabela `clinical_cases` e ganhando tag de *pure_ml*.
*   **Ingestão Massiva (`/api/curadoria/upload-zip`)**: Robôs *Backoffice* podem enviar `.zips` gigantes. A API varre passivamente pastas, higieniza (*snake_case*, ex: "Otite Media Aguda" > `otite_media_aguda`), insere no servidor e automaticamente incrementa o vocabulário sem corromper caminhos da web.
*   **Atlas Sync (`/api/admin/atlas/*`)**: Ciclo completo CRUD de "Soft Delete" (Lixeira para desfazer equívocos no painel web) e reoxigenação de metadados dos Mapas Sensoriais (SVG JSON strings).

---

## 4. O Caminho Evolutivo Traçado

A robustez atestada pelas métricas comprova que o monolito atual serve plenamente aos hospitais e provê resultados assíncronos excelentes. Os passivos arquiteturais estão suprimidos. 
O roteiro de escalada técnica vislumbra agora:
*   Passar das requisições via "Fotos Estáticas" do edge-client para leitura de **Video Stream (Tempo Real)**.
*   Mover parte do peso passivo do ONNX atual do servidor Render diretamente pro Browser do Médico Assistente usando **WebAssembly ($WASM)**.
