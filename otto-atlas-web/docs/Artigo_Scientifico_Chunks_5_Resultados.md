## 4. RESULTADOS

A validação operacional do sistema **OTTOSCOP-IA** não foi medida apenas por acurácia bruta laboratorial, mas por sua robustez intrínseca em evitar a memorização não-clínica de padrões majoritários (*Overfitting*). A abordagem *Human-in-the-loop* demonstrou um profundo impacto qualitativo e quantitativo ao desconstruir classes abrangentes.

### 4.1. Auditoria de Classes e Reestruturação (Otite Média Aguda vs. Crônica)
Na avaliação arquitetural inicial, as métricas apontavam severa confusão algorítmica entre quadros agudos e crônicos, gerando diagnósticos com baixa especificidade — um reflexo de bancos convencionais não focados na evolução temporal estrutural do tímpano. 
O *Curation Hub* auditações sistemáticas propôs a separação estrita taxonômica e segmentação das fotografias. O resultado consistiu em alocar inflamações eritematosas, efusões ativas e opacidades supurativas estritas à classe **Otite Média Aguda (OMA)**, e reservar retração fibrosa crônica, perfuração inativa e placas extensas de miringoesclerose para **Otite Média Crônica (OMC)**.
Essa reparametrização taxonômica resultou em uma redução de *[XX]%* nos falsos-positivos cruzados entre o espectro inflamatório agudo e as sequelas perfurativas estabilizadas, tornando o ecossistema um suporte à decisão confiável para distinção urgente no *point-of-care*.

### 4.2. Performance Preditiva do Modelo (Machine Learning Metrics)
Com a aplicação sistemática de *Data Augmentation* direcionado e *Oversampling* em categorias penalizadas, o motor ONNX evidenciou desempenho sólido no conjunto cego de validação.

*   **Acurácia Global (Accuracy):** O modelo obteve *[XX.X]%* de acurácia agregada nas *[XX]* categorias cadastradas, demonstrando resiliência notável em discriminar achados vitais apesar da redução da fotografia operada pelo *edge-client*.
*   **Especificidade e Sensibilidade (Recall):** Na detecção de condições de alto risco clínico-cirúrgico, a sensibilidade atingiu *[XX.X]%* para [Classe X / Colesteatoma], minimizando de maneira vital o risco de triagem permissiva (falsos-negativos) num Posto de Atenção Primária. A precisão geral (*Precision*) consolidou-se na margem de *[XX.X]%*.
*   **Mitigação de Overfitting e Desempenho Isolado:** O motor preditivo exibiu sua maior confiança na identificação de "[Membrana Timpânica Normal / Cerume Impactado]", alcançando F1-Score respectivo de *[XX.X]* e *[XX.X]*, justificando matematicamente seu uso primário para exclusão rápida de quadros benignos no ambulatório.

A análise da matriz de confusão isolou que os desvios persistem restritos a achados limites (*borderlines*), como diferenciar "Efuso Seroso Espesso" de uma "OMA purulenta inicial", mimetizando o desafio visado por especialistas sêniores, porém muito acima da segurança oferecida por diagnósticos aleatórios comuns à linha de frente desassistida.
