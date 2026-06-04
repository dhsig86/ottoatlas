import { useState, useEffect } from 'react'
import { Lock, Globe, LogOut } from 'lucide-react'
import { AtlasGrid } from './components/AtlasGrid'
import { AtlasQuiz } from './components/AtlasQuiz'
import { AIAnalyzer } from './components/AIAnalyzer'
import { CurationHubV4 } from './components/CurationHubV4'
import { OtoscopyInstructionsModal } from './components/OtoscopyInstructionsModal'
import { CommunityDonation } from './components/CommunityDonation'
import { AdminLoginOverlay } from './components/AdminLoginOverlay'
import { checkExistingSession, signOut } from './services/adminAuth'

function App() {
  const getInitialTab = () => {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    if (tab === 'ia' || tab === 'atlas' || tab === 'quiz' || tab === 'hub' || tab === 'donation') {
      return tab;
    }
    return 'atlas';
  };

  const [viewMode, setViewMode] = useState<'atlas' | 'quiz' | 'ia' | 'hub' | 'donation'>(getInitialTab())
  const [showInstructions, setShowInstructions] = useState(false)
  const isEmbed = new URLSearchParams(window.location.search).get('embed') === 'true'

  // Atualizar URL ao mudar de aba sem recarregar a página
  const handleTabChange = (tab: 'atlas' | 'quiz' | 'ia' | 'hub' | 'donation') => {
    setViewMode(tab);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tab);
    window.history.pushState({}, '', url);
  };

  const handleCopyLink = () => {
    const url = new URL(window.location.href);
    url.searchParams.set('tab', 'ia');
    navigator.clipboard.writeText(url.toString());
    alert('Link exclusivo do Otoscop-IA copiado para a área de transferência!');
  };

  // Auth administrativa via Firebase Google Sign-In
  const [adminEmail, setAdminEmail] = useState<string | null>(null);
  const [showLoginOverlay, setShowLoginOverlay] = useState(false);

  // Verifica se já há sessão Google ativa ao carregar a página
  useEffect(() => {
    checkExistingSession().then((email) => {
      if (email) setAdminEmail(email);
    });
  }, []);

  // Warm-up ping: acorda o backend Render antes do usuário interagir
  useEffect(() => {
    const apiURL = (import.meta.env.VITE_AI_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
    fetch(`${apiURL}/health`, {
      signal: AbortSignal.timeout ? AbortSignal.timeout(20000) : undefined,
    }).catch(() => { /* cold start silencioso */ });
  }, []);

  // PWA handshake: responde ao shell OTTO PWA via postMessage
  useEffect(() => {
    const handleMessage = (e: MessageEvent) => {
      if (e.data?.type === 'otto-context') {
        // Recebeu contexto do PWA (userName, userId, firebaseToken)
        console.log('[OTTO Atlas] Contexto PWA recebido:', e.data.payload?.userName);
        // Responde que o módulo está pronto
        window.parent.postMessage({ type: 'otto-atlas-ready' }, '*');
      }
    };
    window.addEventListener('message', handleMessage);
    // Envia ready pro-ativamente (caso o PWA já tenha mandado o contexto antes do listener)
    if (window.parent !== window) {
      window.parent.postMessage({ type: 'otto-atlas-ready' }, '*');
    }
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  const handleAdminLogout = async () => {
    await signOut();
    setAdminEmail(null);
    if (viewMode === 'hub') handleTabChange('atlas');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center font-sans pb-10">
      {!isEmbed && (
      <header className="w-full bg-brand-600 text-white shadow-md mb-6 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between p-4 md:p-6 gap-4">
          <div className="flex gap-3 md:gap-4 items-center w-full md:w-auto">
            <div className="w-10 h-10 md:w-12 md:h-12 bg-white rounded-xl shadow-inner flex shrink-0 items-center justify-center p-2 transform rotate-3">
              <Globe className="w-6 h-6 md:w-8 md:h-8 text-brand-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-xl md:text-3xl font-black tracking-tight drop-shadow-md truncate">HARTS OTTO ATLAS</h1>
              <p className="text-brand-100 font-medium text-xs md:text-sm tracking-wide truncate">Guia Clínico Interativo</p>
            </div>
          </div>
          
          <div className="w-[calc(100vw-2rem)] md:w-auto overflow-x-auto no-scrollbar pb-1 md:pb-0">
            <nav className="flex gap-2 min-w-max px-1">
              <button 
                onClick={() => handleTabChange('atlas')}
                className={`px-3 py-2 rounded-lg text-sm md:text-base font-medium transition-colors whitespace-nowrap ${viewMode === 'atlas' ? 'bg-white text-brand-600 shadow-sm' : 'text-brand-100 hover:bg-brand-500'}`}
              >
                Acervo
              </button>
              <button 
                onClick={() => handleTabChange('quiz')}
                className={`px-3 py-2 rounded-lg text-sm md:text-base font-medium transition-colors whitespace-nowrap ${viewMode === 'quiz' ? 'bg-white text-brand-600 shadow-sm' : 'text-brand-100 hover:bg-brand-500'}`}
              >
                Quiz Case
              </button>
              <button 
                onClick={() => handleTabChange('donation')}
                className={`px-3 py-2 rounded-lg text-sm md:text-base font-medium transition-colors whitespace-nowrap ${viewMode === 'donation' ? 'bg-white text-brand-600 shadow-sm' : 'text-brand-100 hover:bg-brand-500'}`}
              >
                Colaborar
              </button>
              <div className="flex bg-brand-500 rounded-lg p-1 shadow-inner gap-1">
                <button 
                  onClick={() => handleTabChange('ia')}
                  className={`px-3 py-1.5 rounded-md text-sm md:text-base font-bold transition-colors whitespace-nowrap ${viewMode === 'ia' ? 'bg-yellow-400 text-brand-900 shadow-sm' : 'hover:bg-yellow-400 hover:text-brand-900 text-white'}`}
                >
                  OTOSCOP-IA
                </button>
                <button
                  onClick={handleCopyLink}
                  title="Copiar link de acesso externo"
                  className="px-2 py-1.5 bg-brand-600 hover:bg-brand-700 rounded-md transition-colors flex items-center justify-center text-brand-100 hover:text-white"
                >
                  <Globe className="w-4 h-4" />
                </button>
              </div>
              {adminEmail ? (
                /* Admin logado — mostra ícone ativo + logout rápido */
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleTabChange('hub')}
                    className={`p-2 rounded-lg flex items-center justify-center transition-colors shrink-0 ${viewMode === 'hub' ? 'bg-slate-900 text-white shadow-inner' : 'bg-green-600 text-white hover:bg-slate-800'}`}
                    title={`Admin: ${adminEmail}`}
                  >
                    <Lock className="w-4 h-4 md:w-5 md:h-5" />
                  </button>
                  <button
                    onClick={handleAdminLogout}
                    className="p-2 rounded-lg text-brand-200 hover:bg-brand-500 hover:text-white transition-colors"
                    title="Sair da área administrativa"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                /* Não autenticado — abre overlay de login */
                <button
                  onClick={() => setShowLoginOverlay(true)}
                  className="p-2 rounded-lg flex items-center justify-center transition-colors shrink-0 bg-brand-600 text-brand-200 hover:bg-slate-800 hover:text-white"
                  title="Acesso Administrativo"
                >
                  <Lock className="w-4 h-4 md:w-5 md:h-5" />
                </button>
              )}
            </nav>
          </div>
        </div>
      </header>
      )}

      <main className={`flex-1 w-full max-w-6xl px-4 md:px-6 flex flex-col items-center ${isEmbed ? 'py-4' : ''}`}>
        {viewMode === 'atlas' && (
          <>
            <div className="w-full text-left mb-2 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Acervo de Imagens</h2>
                <p className="text-slate-500 text-sm">Selecione uma imagem para ver os detalhes e marcações.</p>
              </div>
              <button 
                onClick={() => setShowInstructions(true)}
                className="bg-brand-50 hover:bg-brand-100 text-brand-700 px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 border border-brand-200"
              >
                Instruções do Exame
              </button>
            </div>
            <AtlasGrid />
          </>
        )}

        {viewMode === 'quiz' && <AtlasQuiz />}
        {viewMode === 'ia' && <AIAnalyzer />}
        {viewMode === 'hub' && (
          adminEmail
            ? <CurationHubV4 />
            : (
              <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-4">
                <Lock className="w-12 h-12 opacity-20" />
                <p className="font-semibold text-slate-500">Área restrita. Faça login como administrador.</p>
                <button
                  onClick={() => setShowLoginOverlay(true)}
                  className="bg-slate-800 text-white font-bold px-6 py-2.5 rounded-lg hover:bg-slate-700 transition-colors"
                >
                  Fazer login
                </button>
              </div>
            )
        )}
        {viewMode === 'donation' && (
          <div className="w-full flex items-center justify-center mt-6">
            <CommunityDonation />
          </div>
        )}
      </main>

      {showInstructions && (
        <OtoscopyInstructionsModal onClose={() => setShowInstructions(false)} />
      )}

      {showLoginOverlay && (
        <AdminLoginOverlay
          onSuccess={(email) => {
            setAdminEmail(email);
            setShowLoginOverlay(false);
            handleTabChange('hub');
          }}
          onCancel={() => setShowLoginOverlay(false)}
        />
      )}
    </div>
  )
}

export default App
