# CLAUDE.md — ottoatlas

> Contexto para LLMs. Atualizado: 2026-06-03.

## O que é

**OTTO Atlas** é um atlas clínico interativo de imagens otoscópicas para ORL.
Permite navegar por categorias de patologias auriculares, fazer quiz de diagnóstico,
analisar imagens com IA (OTOSCOP-IA), colaborar com imagens da comunidade e editar
marcações SVG sobre imagens.

## Stack

| Camada      | Tecnologia                          |
|-------------|-------------------------------------|
| Frontend    | React 18 + TypeScript + Vite 5      |
| Styling     | Tailwind CSS 3                      |
| Auth        | Firebase Auth (Google SSO)          |
| Database    | NeonDB (Postgres) + Cloudinary (images) |
| IA Backend  | FastAPI (Render) — classificação otoscópica |
| Icons       | lucide-react                        |
| Analytics   | @vercel/analytics                   |
| Deploy      | Vercel (frontend) + Render (backend)|

## Funcionalidades

| Feature            | Componente                | Descrição                                                     |
|--------------------|---------------------------|---------------------------------------------------------------|
| **Acervo (Atlas)** | `AtlasGrid.tsx`           | Grid de categorias com imagens otoscópicas e descrições        |
| **Quiz Case**      | `AtlasQuiz.tsx`           | Quiz de diagnóstico diferencial com imagens                    |
| **OTOSCOP-IA**     | `AIAnalyzer.tsx`          | Upload + análise IA de imagem otoscópica                       |
| **Colaborar**      | `CommunityDonation.tsx`   | Doação comunitária de imagens para o dataset                   |
| **SVG Studio**     | `SVGStudio.tsx`           | Editor de hotspots/marcações SVG sobre imagens do atlas        |
| **Hub Admin**      | `CurationHubV4.tsx`       | Painel admin para curadoria de imagens (requer login Firebase)  |
| **ML Pipeline**    | `AtlasManagerV4.tsx`      | Gestão v4 do atlas com integração ML                           |

## Estrutura de Diretórios

```
ottoatlas/
├── CLAUDE.md                    # ← este arquivo
├── otto-atlas-web/              # App web principal
│   ├── src/
│   │   ├── App.tsx              # Shell principal, roteamento por abas
│   │   ├── components/          # Componentes React
│   │   │   ├── AIAnalyzer.tsx
│   │   │   ├── AdminLoginOverlay.tsx
│   │   │   ├── AtlasGrid.tsx
│   │   │   ├── AtlasManagerV4.tsx
│   │   │   ├── AtlasQuiz.tsx
│   │   │   ├── CommunityDonation.tsx
│   │   │   ├── CurationHubV4.tsx
│   │   │   ├── ImageDetailModal.tsx
│   │   │   ├── MLCuradoria.tsx
│   │   │   ├── OtoscopyInstructionsModal.tsx
│   │   │   └── SVGStudio.tsx
│   │   ├── data/
│   │   │   ├── mockData.ts      # Categorias + imagens do atlas (AtlasItem[])
│   │   │   └── quizData.ts      # Banco de questões do quiz
│   │   ├── lib/
│   │   │   └── firebase.ts      # Inicialização Firebase
│   │   ├── services/
│   │   │   ├── adminAuth.ts     # Auth admin via Firebase Google SSO
│   │   │   └── api.ts           # Chamadas ao backend IA
│   │   └── utils/
│   │       ├── imageCompressor.ts
│   │       └── imageUtils.ts
│   ├── public/
│   │   └── images/
│   │       ├── atlas/           # Imagens legacy
│   │       ├── atlas_new/       # Imagens v2
│   │       ├── atlas_v3/        # Imagens v3 (12 categorias — dataset principal)
│   │       └── atlas_v4/        # Imagens v4 (suplementares)
│   ├── ml_pipeline/             # Scripts Python para pipeline ML
│   ├── scripts/                 # Scripts auxiliares
│   ├── docs/                    # Documentação
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vercel.json              # Config de deploy Vercel
├── OTTO_ML_Dataset/             # Dataset ML processado
├── OTTO_ML_Dataset_Raw/         # Dataset ML bruto
├── frame_extractor/             # Extrator de frames de vídeo otoscópico
└── legacy/                      # Código legado (PostgreSQL)
```

## Dados Clínicos — mockData.ts

O arquivo `src/data/mockData.ts` define o array `atlasData: AtlasItem[]` com 12 categorias:

1. Normal
2. Otite Média Aguda Bacteriana
3. Otite Média Aguda Viral / Inicial
4. Otite Média Crônica Simples
5. Otite Média Crônica Supurativa
6. Timpanoesclerose
7. Otite Externa Fúngica (Otomicose)
8. Otite Externa Aguda Localizada
9. Otite Externa Aguda Difusa
10. Corpo Estranho / Obstrução
11. Otite Média Crônica Colesteatomatosa
12. Otite Média Secretora (OMS)

Cada `AtlasItem` tem: `id`, `pathology`, `images[]`, `description`, `hotspots?[][]`.

## Comandos de Desenvolvimento

```bash
cd otto-atlas-web
npm install          # Instalar dependências
npm run dev          # Dev server (porta 5173 por padrão)
npm run build        # Build de produção (tsc && vite build)
npm run preview      # Preview do build de produção
npm run test         # Executar testes unitários (Vitest)
```

## Variáveis de Ambiente

```bash
# .env (frontend)
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=otto-ecosystem.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=otto-ecosystem
VITE_FIREBASE_STORAGE_BUCKET=otto-ecosystem.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_AI_API_URL=              # URL do backend IA (Render)
VITE_CLOUDINARY_CLOUD_NAME=   # Cloudinary para upload de imagens
```

## Regras de Segurança

- Auth admin via Firebase Google SSO — `adminAuth.ts` verifica e-mail autorizado
- CORS configurado via `vercel.json` — nunca usar `*`
- Imagens de doação passam por compressão (`imageCompressor.ts`) antes do upload
- Sem PII de pacientes nas imagens — dataset anonimizado

## Deploy

- **Frontend**: Vercel (config em `vercel.json`)
- **Backend IA**: Render (endpoint em `VITE_AI_API_URL`)
- Warm-up ping automático no `App.tsx` para acordar backend Render

## Notas para LLMs

1. **mockData.ts é a fonte de verdade** para as categorias visíveis no atlas. Se uma imagem existe em `atlas_v3/` mas não está no mockData, ela é invisível no frontend.
2. **Cada categoria precisa de pelo menos 3 imagens** no array `images[]`.
3. O quiz (`quizData.ts`) é independente do mockData — tem seu próprio banco de questões.
4. O SVG Studio permite criar hotspots sobre imagens, armazenados no campo `hotspots` do AtlasItem.
5. O backend IA (OTOSCOP-IA) é um microserviço separado — não está neste repo.

## Segurança

- Auth admin via Firebase Google SSO — `adminAuth.ts` verifica e-mail autorizado (`VITE_ADMIN_EMAIL` ou fallback `dr.dhsig@gmail.com`)
- CSP `frame-ancestors` restrito via `vercel.json` (PWA + Vercel + Firebase Hosting)
- `X-Content-Type-Options: nosniff` + `Referrer-Policy: strict-origin-when-cross-origin`
- EXIF/GPS strip antes do upload (`imageUtils.ts`) — LGPD ACT-04 compliance
- Compressão client-side antes do upload (`imageCompressor.ts`)
- **Feedback/doação comunitária**: endpoints abertos (sem auth) — intencional para engajamento
- **Curadoria/admin**: endpoints protegidos com `getAuthHeaders()`

### postMessage Origin Validation (Sprint 2026-06-05)

Mensagens `postMessage` recebidas são validadas contra allowlist explícita em `App.tsx`:

```typescript
const ALLOWED_ORIGINS = [
  'https://otto.drdariohart.com',
  'https://ottopwa.vercel.app',
  'https://ottos-plum.vercel.app',
  'http://localhost:5173',
];

// Receber — App.tsx message handler:
if (!ALLOWED_ORIGINS.includes(event.origin)) return;

// Enviar — ready signal:
ALLOWED_ORIGINS.forEach(origin => {
  try { window.parent.postMessage({ type: 'otto-atlas-ready' }, origin); } catch {}
});
```

> ⚠️ **Regra de segurança:** NUNCA usar `'*'` como targetOrigin em `postMessage`. Sempre validar `event.origin` contra `ALLOWED_ORIGINS`.

## Pontos de Atenção para Curadoria

1. ~~**Debris e zip de 116 MB**~~ — ✅ Resolvido: removidos `OTTO_Kaggle_Dataset.zip`, logs, dumps, `__pycache__`
2. ~~**Paths quebrados em produção**~~ — ✅ Corrigido: `OtoscopyInstructionsModal` agora usa `/images/` (copiados para `public/`)
3. ~~**Dead deps (express, heroku scripts)**~~ — ✅ Removidos do `package.json`
4. ~~**`.gitignore` da raíz incompleto**~~ — ✅ Expandido para cobertura completa
5. ~~**Sem postMessage integration**~~ — ✅ Resolvido: `App.tsx` agora implementa handshake PWA com origin validation (`otto-context` / `otto-atlas-ready`)
6. **Testes Automatizados:** Suíte de testes configurada com Vitest e React Testing Library no frontend, cobrindo `data/data.test.ts` (integridade de mockData/quizData) e `components/AtlasQuiz.test.tsx`.
7. **AtlasManagerV4.tsx monolítico** — 728 linhas, candidato a split
8. **`alert()` em api.ts:77** — Mostra alert para usuários finais em erro de predição IA (deveria ser toast)

---

## Changelog

| Data | Mudança | Commit |
|------|---------|--------|
| 2026-06-05 | `App.tsx` — postMessage origin validation adicionada + `console.log` removido | `f35f109` |
