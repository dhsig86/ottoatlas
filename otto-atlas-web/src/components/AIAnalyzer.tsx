import { useState, useRef } from 'react';
import { Upload, Activity, Check, X, Send, Printer } from 'lucide-react';
import { predictOtoscopyImage, sendFeedbackToLegacySystem, PredictionResult } from '../services/api';

export function formatClassName(className: string): string {
  const map: Record<string, string> = {
    'cerume_obstrucao': 'Corpo Estranho / Obstrução (Cerume)',
    'nao_otoscopica': 'Imagem Não Otoscópica',
    'normal': 'Normal',
    'otite_externa_aguda': 'Otite Externa Aguda',
    'otite_media_aguda': 'Otite Média Aguda',
    'otite_media_cronica': 'Otite Média Crônica',
    'otite_media_serosa': 'Otite Média Secretora (OMS)',
    'timpanoesclerose': 'Timpanoesclerose',
    'tubo_de_ventilacao': 'Tubo de Ventilação'
  };
  
  if (map[className]) return map[className];
  
  return className
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function AIAnalyzer() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [predictions, setPredictions] = useState<PredictionResult[] | null>(null);
  
  const [isSending, setIsSending] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState(false);
  
  // Estados para o Form de Feedback (Heroku)
  const [correctDiagnosis, setCorrectDiagnosis] = useState('');
  const [isCorrect, setIsCorrect] = useState<'yes' | 'no' | ''>('');
  const [clinicalCase, setClinicalCase] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
      setPredictions(null);
      setFeedbackSent(false);
    }
  };

  const handlePredict = async () => {
    if (!imageFile) return;
    setIsAnalyzing(true);
    try {
      const results = await predictOtoscopyImage(imageFile);
      setPredictions(results);
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handlePrint = () => {
    if (!predictions || !imagePreview) return;
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      alert('Por favor, libere os pop-ups para imprimir o relatório.');
      return;
    }
    
    const dateStr = new Date().toLocaleString('pt-BR');
    const htmlContent = `
      <html>
        <head>
          <title>Relatório OTOSCOP-IA - OTTO Atlas</title>
          <style>
            body {
              font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
              color: #1e293b;
              margin: 0;
              padding: 40px;
              line-height: 1.5;
            }
            .header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              border-bottom: 2px solid #0f172a;
              padding-bottom: 15px;
              margin-bottom: 30px;
            }
            .title {
              font-size: 24px;
              font-weight: 800;
              color: #0f172a;
              margin: 0;
            }
            .subtitle {
              font-size: 14px;
              color: #64748b;
              margin-top: 5px;
              font-weight: 600;
            }
            .date {
              font-size: 14px;
              color: #64748b;
              text-align: right;
            }
            .content {
              display: flex;
              gap: 30px;
              margin-bottom: 40px;
            }
            .image-container {
              flex: 1;
              max-width: 350px;
              border: 1px solid #cbd5e1;
              border-radius: 8px;
              overflow: hidden;
              background: #f8fafc;
            }
            .image-container img {
              width: 100%;
              height: auto;
              display: block;
            }
            .results-container {
              flex: 1.2;
            }
            .results-title {
              font-size: 16px;
              font-weight: 700;
              color: #475569;
              text-transform: uppercase;
              letter-spacing: 0.05em;
              margin-bottom: 15px;
              border-bottom: 1px solid #e2e8f0;
              padding-bottom: 5px;
            }
            .prediction-item {
              margin-bottom: 15px;
              padding: 10px;
              border: 1px solid #e2e8f0;
              border-radius: 6px;
              background: #f8fafc;
            }
            .prediction-header {
              display: flex;
              justify-content: space-between;
              font-size: 14px;
              font-weight: 600;
              margin-bottom: 5px;
            }
            .prediction-bar-bg {
              width: 100%;
              background: #e2e8f0;
              height: 8px;
              border-radius: 4px;
              overflow: hidden;
            }
            .prediction-bar-fill {
              height: 100%;
              border-radius: 4px;
            }
            .disclaimer {
              background: #fffbeb;
              border: 1px solid #fef3c7;
              color: #78350f;
              padding: 15px;
              border-radius: 8px;
              font-size: 12px;
              line-height: 1.6;
              margin-bottom: 50px;
            }
            .signature-area {
              margin-top: 80px;
              display: flex;
              justify-content: flex-end;
            }
            .signature-line {
              width: 250px;
              border-top: 1px solid #94a3b8;
              text-align: center;
              font-size: 12px;
              color: #64748b;
              padding-top: 5px;
            }
            @media print {
              body {
                padding: 0;
              }
            }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <div class="title">HARTS OTTO ATLAS</div>
              <div class="subtitle">Relatório Clínico — Análise do OTOSCOP-IA</div>
            </div>
            <div class="date">
              <div>Emitido em: ${dateStr}</div>
              <div style="font-size: 12px; margin-top: 5px;">Módulo Auxiliar Diagnóstico ORL</div>
            </div>
          </div>
          
          <div class="content">
            <div class="image-container">
              <img src="${imagePreview}" alt="Imagem Otoscópica Analisada" />
            </div>
            <div class="results-container">
              <div class="results-title">Hipóteses Diagnósticas (Top ${predictions.length})</div>
              ${predictions.map((p, i) => {
                const isTop = i === 0;
                const barColor = isTop ? '#2563eb' : i < 3 ? '#3b82f6' : '#94a3b8';
                const formattedClass = p.class === 'cerume_obstrucao' ? 'Corpo Estranho / Obstrução (Cerume)' :
                                      p.class === 'nao_otoscopica' ? 'Imagem Não Otoscópica' :
                                      p.class === 'normal' ? 'Normal' :
                                      p.class === 'otite_externa_aguda' ? 'Otite Externa Aguda' :
                                      p.class === 'otite_media_aguda' ? 'Otite Média Aguda' :
                                      p.class === 'otite_media_cronica' ? 'Otite Média Crônica' :
                                      p.class === 'otite_media_serosa' ? 'Otite Média Secretora (OMS)' :
                                      p.class === 'timpanoesclerose' ? 'Timpanoesclerose' :
                                      p.class === 'tubo_de_ventilacao' ? 'Tubo de Ventilação' : p.class;
                return `
                  <div class="prediction-item" style="${isTop ? 'border-color: #93c5fd; background: #eff6ff;' : ''}">
                    <div class="prediction-header">
                      <span>${i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`} ${formattedClass}</span>
                      <span style="font-family: monospace;">${p.confidence.toFixed(1)}%</span>
                    </div>
                    <div class="prediction-bar-bg">
                      <div class="prediction-bar-fill" style="width: ${Math.min(p.confidence, 100)}%; background-color: ${barColor};"></div>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
          
          <div class="disclaimer">
            <strong>⚠️ LIMITAÇÃO DE RESPONSABILIDADE / DISCLAIMER CLÍNICO:</strong><br/>
            Este relatório contém sugestões de hipóteses baseadas exclusivamente no processamento de visão computacional da imagem otoscópica fornecida. 
            A predição da inteligência artificial **não substitui, nem objetiva, o diagnóstico final ou definitivo do caso**. 
            O diagnóstico definitivo exige avaliação médica presencial completa realizada por profissional habilitado, com a devida correlação clínica (anamnese detalhada com sintomas como dor, febre, otorreia e otoscopia dinâmica).
          </div>
          
          <div class="signature-area">
            <div>
              <div class="signature-line">Assinatura / CRM do Otorrinolaringologista</div>
            </div>
          </div>
          
          <script>
            window.onload = function() {
              window.print();
              setTimeout(function() { window.close(); }, 500);
            };
          </script>
        </body>
      </html>
    `;
    printWindow.document.write(htmlContent);
    printWindow.document.close();
  };

  const submitFeedback = async () => {
    if (!imageFile || !predictions || predictions.length === 0) return;
    setIsSending(true);
    
    // Preparar os diferenciais como string
    const mainClass = predictions[0].class;
    const diffString = predictions.slice(1).map(p => `${p.class}: ${p.confidence.toFixed(0)}%`).join(', ');

    try {
      const success = await sendFeedbackToLegacySystem(
        imageFile,
        correctDiagnosis || mainClass,
        isCorrect || 'yes',
        mainClass, 
        diffString, // Agora envia diferenciais reais!
        clinicalCase
      );
      
      if (success) {
        setFeedbackSent(true);
        // Limpar após enviar
        setTimeout(() => {
          setImageFile(null);
          setImagePreview(null);
          setPredictions(null);
          setFeedbackSent(false);
          setCorrectDiagnosis('');
          setClinicalCase('');
          setIsCorrect('');
        }, 3000);
      }
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="w-full max-w-4xl bg-white p-6 md:p-8 rounded-2xl shadow-sm border border-slate-200 animate-in fade-in zoom-in">
      <div className="mb-6 text-center break-words">
        <h2 className="text-2xl md:text-3xl font-bold text-slate-800 tracking-tight">
          <Activity className="w-6 h-6 inline-block text-brand-600 mr-2 -mt-1" />
          OTTOscop-IA
        </h2>
        <p className="text-slate-500 mt-1">Carregue uma imagem otoscópica para receber uma segunda opinião e alimentar o modelo de inteligência.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Lado Esquerdo: Upload e Preview */}
        <div className="flex flex-col gap-4">
          {!imagePreview ? (
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="w-full h-64 border-2 border-dashed border-slate-300 hover:border-brand-500 hover:bg-brand-50 rounded-xl flex flex-col items-center justify-center text-slate-500 transition-colors"
            >
              <Upload className="w-10 h-10 mb-2 text-brand-400" />
              <span className="font-medium">Toque para enviar ou tirar foto</span>
            </button>
          ) : (
            <div className="relative w-full aspect-square md:aspect-video rounded-xl overflow-hidden shadow-inner bg-slate-900 group">
              <img src={imagePreview} className="w-full h-full object-contain" alt="Upload prev" />
              <button 
                onClick={() => { setImagePreview(null); setImageFile(null); setPredictions(null); }}
                className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white p-2 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleImageUpload} 
            accept="image/*" 
            className="hidden" 
          />

          {!predictions && imagePreview && (
            <button 
              onClick={handlePredict}
              disabled={isAnalyzing}
              className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-transform hover:-translate-y-0.5"
            >
              {isAnalyzing ? (
                <>Processando IA...</>
              ) : (
                <><Activity className="w-5 h-5" /> Analisar com OTTO Brain</>
              )}
            </button>
          )}
        </div>

        {/* Lado Direito: Resultados e Feedback */}
        <div className="flex flex-col">
          {predictions ? (
            <div className="h-full flex flex-col gap-4">
              <div className="bg-amber-50 border border-amber-200 px-4 py-2.5 rounded-lg text-xs text-amber-800 leading-relaxed">
                <strong>⚠️ Atenção:</strong> Sugestão baseada exclusivamente na imagem. Não substitui avaliação clínica completa (anamnese, otoscopia dinâmica, exame físico).
              </div>

              <div className="bg-brand-50 border border-brand-200 p-5 rounded-xl shadow-sm">
                <span className="block text-brand-600 font-semibold mb-3 text-sm uppercase tracking-wide">
                  Hipóteses Diagnósticas (Top {predictions.length})
                </span>
                
                <div className="flex flex-col gap-2.5">
                  {predictions.map((p, i) => {
                    const isTop = i === 0;
                    const barColor = isTop ? 'bg-brand-500' : i < 3 ? 'bg-brand-300' : 'bg-slate-300';
                    const textWeight = isTop ? 'font-bold text-slate-900' : 'font-medium text-slate-700';
                    const badge = isTop ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`;
                    
                    return (
                      <div key={i} className={`rounded-lg p-3 ${isTop ? 'bg-white border-2 border-brand-300 shadow-sm' : 'bg-white/60 border border-slate-100'}`}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className={`text-sm ${textWeight}`}>
                            <span className="mr-1.5">{badge}</span>
                            {formatClassName(p.class)}
                          </span>
                          <span className={`text-sm font-mono ${isTop ? 'text-brand-600 font-bold' : 'text-slate-500'}`}>
                            {p.confidence.toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
                            style={{ width: `${Math.min(p.confidence, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="mt-4 border-t pt-4">
                  <button
                    onClick={handlePrint}
                    className="w-full bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 py-2.5 px-4 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-all shadow-sm active:scale-95"
                  >
                    <Printer className="w-4 h-4 text-slate-500" /> Imprimir Relatório Clínico
                  </button>
                </div>
              </div>

              <div className="bg-white border text-left border-slate-200 p-5 rounded-xl shadow-sm flex-1">
                <h3 className="font-bold text-slate-700 mb-3 border-b pb-2">Validar Diagnóstico (Retreinamento)</h3>
                
                <div className="mb-3">
                  <label className="block text-sm font-medium text-slate-600 mb-1">A predição está correta?</label>
                  <select 
                    value={isCorrect} 
                    onChange={e => setIsCorrect(e.target.value as 'yes' | 'no')}
                    className="w-full border-slate-300 rounded-lg shadow-sm p-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="" disabled>Selecione...</option>
                    <option value="yes">Sim</option>
                    <option value="no">Não</option>
                  </select>
                </div>

                {isCorrect === 'no' && (
                  <div className="mb-3 animate-in fade-in slide-in-from-top-2">
                    <label className="block text-sm font-medium text-slate-600 mb-1">Qual é o diagnóstico correto?</label>
                    <input 
                      type="text" 
                      value={correctDiagnosis}
                      onChange={e => setCorrectDiagnosis(e.target.value)}
                      placeholder="Ex: Cerume Impactado"
                      className="w-full border-slate-300 rounded-lg shadow-sm p-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                  </div>
                )}

                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-600 mb-1">Notas Clínicas Breves (Opcional)</label>
                  <input 
                    type="text" 
                    value={clinicalCase}
                    onChange={e => setClinicalCase(e.target.value)}
                    placeholder="Paciente de 30 anos com dor etc..."
                    className="w-full border-slate-300 rounded-lg shadow-sm p-2 focus:ring-brand-500 focus:border-brand-500"
                  />
                </div>

                <button 
                  onClick={submitFeedback}
                  disabled={isSending || isCorrect === '' || (isCorrect === 'no' && correctDiagnosis === '')}
                  className="w-full bg-brand-500 hover:bg-brand-600 disabled:bg-slate-300 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-transform hover:-translate-y-0.5"
                >
                  {isSending ? 'Salvando no Servidor...' : <><Send className="w-5 h-5"/> Enviar ao Banco de Dados</>}
                </button>
                
                {feedbackSent && (
                  <p className="text-green-600 text-sm font-semibold flex items-center justify-center gap-1 mt-3 animate-in bounce-in">
                    <Check className="w-4 h-4"/> Feedback enviado com sucesso para a base!
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="h-full border-2 border-dashed border-slate-200 rounded-xl flex items-center justify-center p-6 text-center bg-slate-50 text-slate-400">
              <p>Os resultados e o painel de treinamento do modelo aparecerão aqui após a análise da imagem.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
