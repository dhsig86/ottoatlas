import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, AlertCircle, FileImage, Send, X, Map, Undo2, CheckCircle2 } from 'lucide-react';
import { compressImage } from '../utils/imageCompressor';
import { getApiBase } from '../services/api';

interface Point { x: number; y: number }
interface SvgHotspot { id: string; label: string; path: string; color?: string; }

export function CommunityDonation() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [diagnostic, setDiagnostic] = useState('');
  const [clinicalCase, setClinicalCase] = useState('');
  
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // --- SVG Studio State ---
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [svgPolygons, setSvgPolygons] = useState<SvgHotspot[]>([]);
  const [currentPoints, setCurrentPoints] = useState<Point[]>([]);
  const [svgViewBox, setSvgViewBox] = useState("0 0 1024 1024");
  const activeColor = "#10b981"; // Neon Green default para doadores
  const imageRef = useRef<HTMLImageElement>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).slice(0, 10);
      setSelectedFiles(newFiles);
      
      const newPreviews = newFiles.map(file => URL.createObjectURL(file));
      setImagePreviews(newPreviews);
      
      setUploadSuccess(false);
      setErrorMsg('');
      setSvgPolygons([]); // reset SVG 
    }
  };

  const removeFile = (index: number) => {
    const updatedFiles = [...selectedFiles];
    updatedFiles.splice(index, 1);
    setSelectedFiles(updatedFiles);
    
    const updatedPreviews = [...imagePreviews];
    updatedPreviews.splice(index, 1);
    setImagePreviews(updatedPreviews);
    if(index === 0) setSvgPolygons([]);
  };

  const clearForm = () => {
    setSelectedFiles([]);
    setImagePreviews([]);
    setDiagnostic('');
    setClinicalCase('');
    setSvgPolygons([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDonate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFiles.length === 0 || !diagnostic) return;
    
    setIsUploading(true);
    setErrorMsg('');
    
    try {
      const formData = new FormData();
      for (const file of selectedFiles) {
        const optimized = await compressImage(file);
        formData.append('files', optimized);
      }
      formData.append('diagnostic', diagnostic);
      if (clinicalCase) formData.append('clinical_case', clinicalCase);
      if (svgPolygons.length > 0) formData.append('svg_json', JSON.stringify(svgPolygons));
      
      const endpoint = `${getApiBase()}/api/curadoria/donate`;

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) throw new Error('Falha de conexão com a Cloud.');
      
      const data = await response.json();
      if (data.error) throw new Error(data.error);
      
      setUploadSuccess(true);
      setTimeout(clearForm, 4000);
      
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Erro ao processar envio.');
    } finally {
      setIsUploading(false);
    }
  };

  // --- Funções de Desenho SVG ---
  const handleCanvasClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!imageRef.current) return;
    const svg = e.currentTarget;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    const loc = pt.matrixTransform(ctm.inverse());
    setCurrentPoints([...currentPoints, { x: Math.round(loc.x), y: Math.round(loc.y) }]);
  };

  const generateSmoothPath = (pts: Point[]) => {
    if (pts.length === 0) return '';
    if (pts.length === 1) return `M ${pts[0].x},${pts[0].y} m -8,0 a 8,8 0 1,0 16,0 a 8,8 0 1,0 -16,0`;
    let path = `M ${pts[0].x},${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) {
        const p1 = pts[i - 1];
        const p2 = pts[i];
        const xc = (p1.x + p2.x) / 2;
        const yc = (p1.y + p2.y) / 2;
        path += ` Q ${p1.x},${p1.y} ${xc},${yc}`;
    }
    path += ` L ${pts[pts.length - 1].x},${pts[pts.length - 1].y} Z`;
    return path;
  };

  const handleFinishPolygon = () => {
    if (currentPoints.length === 0) return;
    const label = prompt("Qual estrutura anatômica você acabou de desenhar? (ex: Cabo do Martelo, Perfuração)") || "Estrutura Marcada";
    setSvgPolygons([...svgPolygons, { 
        id: `m_${Date.now()}`, 
        label, 
        path: generateSmoothPath(currentPoints), 
        color: activeColor 
    }]);
    setCurrentPoints([]);
  };

  const deleteSavedPolygon = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if(!confirm("Remover estrutura?")) return;
    setSvgPolygons(svgPolygons.filter((s) => s.id !== id));
  };

  return (
    <div className="w-full max-w-4xl bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-100 p-6 md:p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* ===== MESA DE EDIÇÃO SVG (OVERLAY) ===== */}
      {isDrawingMode && imagePreviews.length > 0 && (
         <div className="fixed inset-0 z-50 bg-slate-950 flex flex-col pt-[72px]">
             <div className="flex justify-between items-center bg-slate-900 border-b border-slate-800 p-4 shrink-0">
                  <div className="flex items-center gap-3">
                      <button onClick={() => { setIsDrawingMode(false); setCurrentPoints([]); }} className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition font-bold text-sm flex gap-2 items-center"><X className="w-4 h-4"/> Sair e Aplicar</button>
                      <h3 className="text-slate-300 font-bold ml-4 hidden md:block">Studio SVG - Mapeamento de Foco</h3>
                  </div>
                  
                  <div className="flex items-center gap-3">
                      {svgPolygons.length > 0 && <span className="text-brand-400 font-bold text-xs bg-brand-900/40 px-3 py-1 rounded">{svgPolygons.length} Salvo(s)</span>}
                      <button onClick={() => setCurrentPoints(currentPoints.slice(0, -1))} disabled={currentPoints.length === 0} className="text-slate-400 bg-slate-800 hover:bg-slate-700 disabled:opacity-30 p-2 rounded transition"><Undo2 className="w-4 h-4" /></button>
                      <button onClick={handleFinishPolygon} disabled={currentPoints.length === 0} className="bg-brand-600 hover:bg-brand-500 text-white font-bold px-4 py-2 rounded transition flex items-center gap-2"><CheckCircle2 className="w-4 h-4" /> Finalizar Contorno</button>
                  </div>
              </div>
              <div className="flex-1 bg-black relative flex justify-center items-center overflow-hidden">
                   <img 
                       ref={imageRef} 
                       src={imagePreviews[0]} 
                       alt="Canvas" 
                       onLoad={(e) => setSvgViewBox(`0 0 ${e.currentTarget.naturalWidth} ${e.currentTarget.naturalHeight}`)}
                       className="w-full h-full object-contain pointer-events-none" 
                   />
                   <svg 
                       viewBox={svgViewBox} 
                       preserveAspectRatio="xMidYMid meet"
                       className="absolute inset-0 w-full h-full cursor-crosshair z-10"
                       onClick={handleCanvasClick}
                   >
                       {svgPolygons.map((sp) => (
                           <g key={sp.id} className="pointer-events-auto">
                               <path d={sp.path} fillRule="evenodd" className="fill-transparent stroke-[4]" style={{ stroke: sp.color }} />
                               <title>{sp.label}</title>
                           </g>
                       ))}
                       {currentPoints.length > 0 && (
                           <path d={generateSmoothPath(currentPoints)} fill="transparent" stroke={activeColor} strokeWidth="4" strokeDasharray="6 6" />
                       )}
                       {currentPoints.map((p, idx) => ( 
                           <circle key={idx} cx={p.x} cy={p.y} r="8" fill={activeColor} stroke="#000" strokeWidth="2" /> 
                       ))}
                   </svg>
              </div>
         </div>
      )}

      {/* ===== HEADER NATIVA ===== */}
      <div className="flex flex-col items-center text-center mb-8">
        <div className="w-16 h-16 bg-brand-100 text-brand-600 rounded-full flex items-center justify-center mb-4 shadow-inner">
          <UploadCloud size={32} />
        </div>
        <h2 className="text-2xl font-bold text-slate-800">Colaboratório do Atlas</h2>
        <p className="text-slate-500 mt-2 max-w-lg">
          Compartilhe casos otoscópicos validados da sua prática clínica. Você pode inclusive mapear as estruturas do seu exame!
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
        {/* Lado Esquerdo: Imagem */}
        <div className="flex flex-col">
          <label className="text-sm font-semibold text-slate-700 mb-2">Imagens do Exame (Até 10 fotos)</label>
          
          <div 
            onClick={() => !isUploading && fileInputRef.current?.click()}
            className={`
              relative flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-6
              transition-all duration-300 min-h-[16rem] cursor-pointer overflow-hidden

              ${isUploading ? 'opacity-50 cursor-not-allowed border-slate-300 bg-slate-50' : 'hover:border-brand-500 hover:bg-brand-50 border-slate-300'}
              ${imagePreviews.length > 0 ? 'border-none p-0 bg-slate-50' : ''}
            `}
            style={imagePreviews.length > 0 ? { cursor: 'default' } : undefined}
          >
            {imagePreviews.length > 0 ? (
              <div 
                className="absolute inset-0 p-2 overflow-y-auto w-full h-full flex flex-col gap-2 rounded-xl"
                onClick={(e) => e.stopPropagation()}
              >
                {/* PREVIEW DA IMAGEM PRINCIPAL (Com Suporte a SVG Mapeamento) */}
                 <div className="relative group rounded-xl bg-black overflow-hidden shadow-md flex-shrink-0 w-full" style={{ aspectRatio: '1/1' }}>
                    <img src={imagePreviews[0]} alt="Principal" className="w-full h-full object-cover" />
                    
                    {/* Botões do Layer da Imagem 0 */}
                    <button type="button" onClick={() => removeFile(0)} className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded p-1.5 shadow z-20">
                      <X size={16} />
                    </button>
                    
                    <button 
                      onClick={() => setIsDrawingMode(true)}
                      className={`absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center justify-center gap-2 px-4 py-2 rounded-full font-bold text-sm shadow-xl transition-all z-20 hover:scale-105 border-2 ${svgPolygons.length > 0 ? 'bg-brand-600 hover:bg-brand-500 text-white border-brand-400' : 'bg-slate-900/80 hover:bg-slate-900 text-slate-100 border-slate-700 backdrop-blur'}`}
                    >
                      <Map className="w-4 h-4" /> {svgPolygons.length > 0 ? `${svgPolygons.length} Estrutura(s) Mapeada(s)` : 'Mapear Lesão'}
                    </button>
                 </div>
                 
                 {/* GRADE DE IMAGENS ADICIONAIS */}
                 {imagePreviews.length > 1 && (
                     <div className="grid grid-cols-4 gap-2">
                       {imagePreviews.slice(1).map((preview, i) => (
                         <div key={i+1} className="relative group rounded-lg bg-black overflow-hidden aspect-square border border-slate-200">
                           <img src={preview} alt={`Preview ${i+1}`} className="w-full h-full object-cover opacity-80" />
                           <button type="button" onClick={() => removeFile(i+1)} className="absolute top-1 right-1 bg-red-500 text-white rounded opacity-0 group-hover:opacity-100 p-0.5">
                             <X size={12} />
                           </button>
                         </div>
                       ))}
                       {imagePreviews.length < 10 && !isUploading && (
                         <div onClick={() => fileInputRef.current?.click()} className="flex items-center justify-center border-2 border-dashed border-slate-300 rounded-lg aspect-square cursor-pointer hover:bg-slate-100 text-slate-400">
                           + 
                         </div>
                       )}
                     </div>
                 )}
              </div>
            ) : (
              <div className="flex flex-col items-center text-center">
                <FileImage size={40} className="text-slate-400 mb-4" />
                <p className="text-slate-600 font-medium">Clique para escolher as imagens</p>
                <p className="text-slate-400 text-xs mt-2">Formatos suportados: JPG, PNG</p>
              </div>
            )}
            
            <input 
              type="file" 
              multiple
              ref={fileInputRef} 
              onChange={handleFileSelect} 
              accept="image/jpeg, image/png, image/jpg" 
              className="hidden" 
              disabled={isUploading}
            />
          </div>
        </div>

        {/* Lado Direito: Formulário */}
        <form onSubmit={handleDonate} className="flex flex-col justify-between">
          <div className="space-y-4">
            <div>
              <label htmlFor="diagnostic" className="block text-sm font-semibold text-slate-700 mb-1">
                Diagnóstico Mestre <span className="text-red-500">*</span>
              </label>
              <input
                id="diagnostic"
                required
                type="text"
                disabled={isUploading || uploadSuccess}
                placeholder="Ex: Otite Média Crônica Supurativa"
                value={diagnostic}
                onChange={(e) => setDiagnostic(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
              />
            </div>
            
            <div>
              <label htmlFor="clinicalCase" className="block text-sm font-semibold text-slate-700 mb-1">
                Quadro Clínico <span className="text-slate-400 font-normal">(Opcional)</span>
              </label>
              <textarea
                id="clinicalCase"
                disabled={isUploading || uploadSuccess}
                rows={3}
                placeholder="Ex: Paciente com otorreia recorrente desde a infância, indolor..."
                value={clinicalCase}
                onChange={(e) => setClinicalCase(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-500 outline-none transition-all resize-none"
              />
            </div>

            {svgPolygons.length > 0 && (
                <div className="bg-emerald-50 rounded-lg border border-emerald-200 p-3 flex flex-col gap-2">
                    <p className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1"><Map className="w-3 h-3"/> {svgPolygons.length} Polígonos Salvos</p>
                    <div className="flex flex-wrap gap-1">
                        {svgPolygons.map(p => (
                            <span key={p.id} className="bg-emerald-100 text-emerald-700 text-xs px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
                                {p.label}
                                <button type="button" onClick={(e) => deleteSavedPolygon(p.id, e)} className="hover:text-red-500"><X size={10}/></button>
                            </span>
                        ))}
                    </div>
                </div>
            )}
          </div>

          <div className="mt-6">
            {errorMsg && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm flex items-start gap-2">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                <p>{errorMsg}</p>
              </div>
            )}
            
            {uploadSuccess ? (
              <div className="w-full py-4 bg-emerald-50 text-emerald-700 rounded-xl font-bold flex items-center justify-center gap-2 border border-emerald-200 shadow-sm">
                <CheckCircle size={20} />
                Doação recebida pelo Atlas!
              </div>
            ) : (
              <button
                type="submit"
                disabled={selectedFiles.length === 0 || !diagnostic || isUploading}
                className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:hover:bg-brand-600 text-white font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg disabled:shadow-none"
              >
                {isUploading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Enviando aos Servidores...
                  </>
                ) : (
                  <>
                    <Send size={18} />
                    Enviar Contribuição
                  </>
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

