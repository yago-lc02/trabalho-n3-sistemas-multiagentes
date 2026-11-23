/**
 * Aplicação Frontend para o Workshop FASOFT UniRV
 * Gestor Inteligente de Estudos e Simulador de Provas Multiagentes
 */

class StudyApp {
  constructor() {
    this.currentData = null;
    this.tipoEntrada = 'pdf'; // 'pdf' | 'text'
    this.respostasUsuario = {};
    this.providerAtual = 'demo';
    
    this.init();
  }

  async init() {
    await this.carregarConfiguracao();
    // Carrega o exemplo demonstrativo inicial por padrão para visualização imediata da interface
    await this.carregarExemploDemo();
  }

  async carregarConfiguracao() {
    try {
      const resp = await fetch('/api/config');
      if (resp.ok) {
        const config = await resp.json();
        this.providerAtual = config.current_provider || 'demo';
        const sel = document.getElementById('provider-select');
        if (sel) {
          sel.value = this.providerAtual;
        }
        this.atualizarTextoProvedor(this.providerAtual);
      }
    } catch (e) {
      console.warn("Falha ao carregar /api/config:", e);
    }
  }

  atualizarTextoProvedor(provider) {
    const el = document.getElementById('status-env-text');
    if (!el) return;
    const labels = {
      'demo': 'Modo Demonstração Instantâneo (Garantia de Velocidade)',
      'ollama': 'Modo Local / 100% Offline (Ollama: llama3.2)',
      'gemini': 'Modo Nuvem Google (Gemini 1.5 Flash via .env)',
      'openai': 'Modo Nuvem OpenAI (GPT-4o-mini via .env)'
    };
    el.textContent = `Provedor Ativo: ${labels[provider] || provider}`;
  }

  mudarProvedor(val) {
    this.providerAtual = val;
    this.atualizarTextoProvedor(val);
  }

  selecionarAbaEntrada(tipo) {
    this.tipoEntrada = tipo;
    const btnPdf = document.getElementById('tab-btn-pdf');
    const btnText = document.getElementById('tab-btn-text');
    const areaPdf = document.getElementById('area-upload-pdf');
    const areaText = document.getElementById('area-colar-texto');

    if (tipo === 'pdf') {
      btnPdf.className = "text-[11px] px-2 py-0.5 rounded font-medium bg-slate-900 text-white";
      btnText.className = "text-[11px] px-2 py-0.5 rounded font-medium text-slate-600 hover:bg-slate-100";
      areaPdf.classList.remove('hidden');
      areaText.classList.add('hidden');
    } else {
      btnText.className = "text-[11px] px-2 py-0.5 rounded font-medium bg-slate-900 text-white";
      btnPdf.className = "text-[11px] px-2 py-0.5 rounded font-medium text-slate-600 hover:bg-slate-100";
      areaText.classList.remove('hidden');
      areaPdf.classList.add('hidden');
    }
  }

  atualizarNomeArquivo(input) {
    const label = document.getElementById('label-arquivo');
    if (input.files && input.files[0]) {
      label.textContent = `Arquivo selecionado: ${input.files[0].name} (${(input.files[0].size / 1024).toFixed(1)} KB)`;
    } else {
      label.textContent = "Clique ou arraste um PDF aqui";
    }
  }

  async carregarExemploDemo() {
    try {
      const resp = await fetch('/api/demo-data');
      if (resp.ok) {
        const data = await resp.json();
        this.renderizarResultados(data);
      }
    } catch (e) {
      console.error("Erro ao carregar exemplo demo:", e);
    }
  }

  mudarAbaResultado(aba) {
    const abas = ['resumo', 'simulado', 'cronograma'];
    abas.forEach(nome => {
      const elConteudo = document.getElementById(`conteudo-${nome}`);
      const elNav = document.getElementById(`tab-nav-${nome}`);
      
      if (nome === aba) {
        elConteudo.classList.remove('hidden');
        elNav.className = "py-3 px-1 border-b-2 border-[#1E3A8A] font-semibold text-xs text-[#1E3A8A] flex items-center space-x-1.5";
      } else {
        elConteudo.classList.add('hidden');
        elNav.className = "py-3 px-1 border-b-2 border-transparent font-medium text-xs text-slate-500 hover:text-slate-800 hover:border-slate-300 flex items-center space-x-1.5";
      }
    });
  }

  async processarMaterial(evt) {
    evt.preventDefault();
    const btnSubmit = document.getElementById('btn-submit');
    const boxProgresso = document.getElementById('progresso-agentes');
    const barra = document.getElementById('barra-progresso');
    const statusTxt = document.getElementById('progresso-percentual');

    const disciplina = document.getElementById('disciplina').value;
    const dias = parseInt(document.getElementById('dias').value) || 5;
    const horas = parseFloat(document.getElementById('horas').value) || 2.0;

    btnSubmit.disabled = true;
    btnSubmit.classList.add('opacity-50', 'cursor-not-allowed');
    boxProgresso.classList.remove('hidden');
    barra.style.width = '20%';
    statusTxt.textContent = "Iniciando Agente 1 (Sintetizador)...";

    // Simula visualmente o pipeline sequencial CrewAI se for demo ou espera a requisição
    let timer = setInterval(() => {
      let currentW = parseInt(barra.style.width) || 20;
      if (currentW < 85) {
        barra.style.width = (currentW + 15) + '%';
        if (currentW > 30 && currentW <= 60) {
          statusTxt.textContent = "Agente 2 (Banca Examinadora) elaborando questões...";
        } else if (currentW > 60) {
          statusTxt.textContent = "Agente 3 (Tutor Espaçado) construindo cronograma...";
        }
      }
    }, 400);

    try {
      let data = null;

      if (this.tipoEntrada === 'pdf') {
        const fileInput = document.getElementById('arquivo-pdf');
        if (!fileInput.files || !fileInput.files[0]) {
          alert("Por favor, selecione um arquivo PDF ou mude para a aba 'Colar Texto'.");
          clearInterval(timer);
          boxProgresso.classList.add('hidden');
          btnSubmit.disabled = false;
          btnSubmit.classList.remove('opacity-50', 'cursor-not-allowed');
          return;
        }

        const formData = new FormData();
        formData.append('disciplina', disciplina);
        formData.append('dias_ate_prova', dias);
        formData.append('horas_por_dia', horas);
        formData.append('provider', this.providerAtual);
        formData.append('arquivo', fileInput.files[0]);

        const resp = await fetch('/api/processar-pdf', {
          method: 'POST',
          body: formData
        });

        if (!resp.ok) {
          const errData = await resp.json();
          throw new Error(errData.detail || "Erro ao processar PDF");
        }
        data = await resp.json();

      } else {
        const texto = document.getElementById('texto-material').value;
        if (!texto.trim()) {
          alert("Por favor, digite ou cole o texto do material.");
          clearInterval(timer);
          boxProgresso.classList.add('hidden');
          btnSubmit.disabled = false;
          btnSubmit.classList.remove('opacity-50', 'cursor-not-allowed');
          return;
        }

        const resp = await fetch('/api/processar-texto', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            disciplina: disciplina,
            dias_ate_prova: dias,
            horas_por_dia: horas,
            texto_material: texto,
            provider: this.providerAtual
          })
        });

        if (!resp.ok) {
          const errData = await resp.json();
          throw new Error(errData.detail || "Erro ao processar texto");
        }
        data = await resp.json();
      }

      barra.style.width = '100%';
      statusTxt.textContent = "Orquestração concluída!";
      setTimeout(() => {
        clearInterval(timer);
        boxProgresso.classList.add('hidden');
        this.renderizarResultados(data);
      }, 500);

    } catch (err) {
      clearInterval(timer);
      boxProgresso.classList.add('hidden');
      alert(`Falha no processamento com os agentes: ${err.message}`);
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.classList.remove('opacity-50', 'cursor-not-allowed');
    }
  }

  renderizarResultados(data) {
    this.currentData = data;
    this.respostasUsuario = {};

    // 1. Resumo
    const resumo = data.resumo || {};
    document.getElementById('resumo-titulo').textContent = resumo.titulo || data.disciplina;
    document.getElementById('resumo-visao-geral').textContent = resumo.visao_geral || "";
    
    const topicos = resumo.topicos || [];
    document.getElementById('badge-topicos').textContent = topicos.length;
    const listaTopicosEl = document.getElementById('lista-topicos');
    listaTopicosEl.innerHTML = '';

    topicos.forEach(t => {
      let badgeClass = "bg-slate-100 text-slate-700 border-slate-200";
      if (t.complexidade === 'Alta') badgeClass = "bg-red-50 text-red-700 border-red-200";
      else if (t.complexidade === 'Média') badgeClass = "bg-amber-50 text-amber-700 border-amber-200";
      else if (t.complexidade === 'Baixa') badgeClass = "bg-emerald-50 text-emerald-700 border-emerald-200";

      const pontosHtml = (t.pontos_criticos || []).map(p => `
        <li class="flex items-start space-x-1.5 text-xs text-slate-600">
          <span class="text-slate-400">&bull;</span>
          <span>${p}</span>
        </li>
      `).join('');

      const card = document.createElement('div');
      card.className = "border border-slate-200 rounded p-3.5 bg-slate-50/50 space-y-2";
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <h5 class="text-xs font-semibold text-slate-900">${t.nome}</h5>
          <span class="text-[10px] font-semibold px-2 py-0.5 rounded border ${badgeClass}">
            Complexidade ${t.complexidade}
          </span>
        </div>
        <p class="text-xs text-slate-600 leading-relaxed">${t.definicao}</p>
        <ul class="space-y-1 pt-1 border-t border-slate-200/60">
          ${pontosHtml}
        </ul>
      `;
      listaTopicosEl.appendChild(card);
    });

    // 2. Simulado
    const simulado = data.simulado || {};
    const questoesObj = simulado.questoes_multipla_escolha || [];
    const containerObj = document.getElementById('lista-questoes-objetivas');
    containerObj.innerHTML = '';
    document.getElementById('box-pontuacao').classList.add('hidden');

    questoesObj.forEach((q, idx) => {
      const qDiv = document.createElement('div');
      qDiv.id = `q-card-${q.id}`;
      qDiv.className = "border border-slate-200 rounded-lg p-4 bg-white shadow-sm space-y-3";
      
      let alternativasHtml = '';
      for (const [letra, texto] of Object.entries(q.alternativas || {})) {
        alternativasHtml += `
          <label class="flex items-start space-x-2.5 p-2 rounded border border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors text-xs text-slate-700" id="alt-box-${q.id}-${letra}">
            <input type="radio" name="questao-${q.id}" value="${letra}" onchange="window.app.selecionarResposta(${q.id}, '${letra}')" class="mt-0.5 text-[#1E3A8A] focus:ring-0">
            <span class="font-semibold text-slate-900">${letra})</span>
            <span class="leading-relaxed">${texto}</span>
          </label>
        `;
      }

      qDiv.innerHTML = `
        <div class="flex items-start justify-between">
          <span class="text-xs font-bold text-[#1E3A8A]">Questão ${idx + 1} (Objetiva)</span>
          <span id="q-status-${q.id}" class="text-[11px] font-medium text-slate-400">Não respondida</span>
        </div>
        <p class="text-xs text-slate-800 leading-relaxed font-medium">${q.enunciado}</p>
        <div class="space-y-2 pt-1">
          ${alternativasHtml}
        </div>
        <div id="q-feedback-${q.id}" class="hidden p-3 rounded border text-xs leading-relaxed mt-2">
          <!-- Comentário do gabarito -->
        </div>
      `;
      containerObj.appendChild(qDiv);
    });

    // Questões Discursivas
    const questoesDisc = simulado.questoes_discursivas || [];
    const containerDisc = document.getElementById('lista-questoes-discursivas');
    containerDisc.innerHTML = '';

    questoesDisc.forEach((qd, idx) => {
      const discDiv = document.createElement('div');
      discDiv.className = "border border-slate-200 rounded-lg p-4 bg-white shadow-sm space-y-3";
      discDiv.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-slate-800">Questão Discursiva ${idx + 1}</span>
          <button onclick="window.app.toggleRespostaEsperada(${qd.id})" class="text-xs text-[#1E3A8A] hover:underline font-medium">
            Ver resposta esperada
          </button>
        </div>
        <p class="text-xs text-slate-800 leading-relaxed font-medium">${qd.enunciado}</p>
        <textarea rows="3" placeholder="Redija seu rascunho de resposta aqui para fixação..."
          class="w-full text-xs p-2.5 border border-slate-200 rounded focus:border-slate-800 focus:outline-none"></textarea>
        <div id="resp-disc-${qd.id}" class="hidden p-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 whitespace-pre-line leading-relaxed">
          <strong class="block text-slate-900 mb-1">Gabarito Conceitual do Professor:</strong>
          ${qd.resposta_esperada}
        </div>
      `;
      containerDisc.appendChild(discDiv);
    });

    // 3. Cronograma
    const cronograma = data.cronograma || {};
    document.getElementById('cronograma-estrategia').textContent = cronograma.resumo_estrategia || "";
    
    const diasList = cronograma.dias || [];
    document.getElementById('badge-dias').textContent = `${diasList.length} dias`;
    const containerDias = document.getElementById('lista-dias-cronograma');
    containerDias.innerHTML = '';

    diasList.forEach(d => {
      const ativHtml = (d.atividades || []).map(a => `
        <li class="flex items-start space-x-2 text-xs text-slate-700">
          <span class="text-[#1E3A8A] font-bold">&bull;</span>
          <span>${a}</span>
        </li>
      `).join('');

      const topicosBadges = (d.topicos_alvo || []).map(t => `
        <span class="inline-block text-[10px] bg-slate-100 text-slate-700 border border-slate-200 px-1.5 py-0.5 rounded">
          ${t}
        </span>
      `).join(' ');

      const diaCard = document.createElement('div');
      diaCard.className = "border border-slate-200 rounded-lg p-4 bg-white shadow-sm space-y-2";
      diaCard.innerHTML = `
        <div class="flex items-center justify-between border-b border-slate-100 pb-2">
          <div class="flex items-center space-x-2">
            <span class="bg-[#1E3A8A] text-white text-[11px] font-bold px-2 py-0.5 rounded">
              Dia ${d.dia}
            </span>
            <h5 class="text-xs font-semibold text-slate-900">${d.foco_principal}</h5>
          </div>
          <span class="text-xs font-mono text-slate-500">${d.horas_previstas}h de estudo</span>
        </div>
        <div class="pt-1">
          <div class="text-[11px] text-slate-500 mb-1.5">Tópicos priorizados: ${topicosBadges}</div>
          <ul class="space-y-1.5">
            ${ativHtml}
          </ul>
        </div>
      `;
      containerDias.appendChild(diaCard);
    });
  }

  selecionarResposta(questaoId, letra) {
    this.respostasUsuario[questaoId] = letra;
    const statusEl = document.getElementById(`q-status-${questaoId}`);
    if (statusEl) {
      statusEl.textContent = `Marcada: ${letra}`;
      statusEl.className = "text-[11px] font-semibold text-slate-700";
    }
  }

  corrigirSimulado() {
    if (!this.currentData || !this.currentData.simulado) return;
    const questoes = this.currentData.simulado.questoes_multipla_escolha || [];
    let acertos = 0;

    questoes.forEach(q => {
      const respUser = this.respostasUsuario[q.id];
      const feedbackEl = document.getElementById(`q-feedback-${q.id}`);
      const statusEl = document.getElementById(`q-status-${q.id}`);
      
      // Reseta classes visuais das alternativas
      for (const letra of ['A', 'B', 'C', 'D']) {
        const altBox = document.getElementById(`alt-box-${q.id}-${letra}`);
        if (altBox) {
          altBox.className = "flex items-start space-x-2.5 p-2 rounded border border-slate-200 text-xs text-slate-700";
        }
      }

      if (respUser === q.resposta_correta) {
        acertos++;
        if (statusEl) {
          statusEl.textContent = "✓ Correta";
          statusEl.className = "text-[11px] font-semibold text-emerald-700";
        }
      } else {
        if (statusEl) {
          statusEl.textContent = "✕ Incorreta";
          statusEl.className = "text-[11px] font-semibold text-red-600";
        }
      }

      // Destaca alternativa correta em verde suave e incorreta marcada em vermelho suave
      const boxCorreta = document.getElementById(`alt-box-${q.id}-${q.resposta_correta}`);
      if (boxCorreta) {
        boxCorreta.className = "flex items-start space-x-2.5 p-2 rounded border border-emerald-300 bg-emerald-50 text-xs text-emerald-900 font-medium";
      }
      if (respUser && respUser !== q.resposta_correta) {
        const boxErrada = document.getElementById(`alt-box-${q.id}-${respUser}`);
        if (boxErrada) {
          boxErrada.className = "flex items-start space-x-2.5 p-2 rounded border border-red-300 bg-red-50 text-xs text-red-900";
        }
      }

      // Exibe gabarito comentado
      if (feedbackEl) {
        feedbackEl.classList.remove('hidden');
        feedbackEl.className = "p-3 rounded border text-xs leading-relaxed mt-2 bg-slate-50 border-slate-200 text-slate-800";
        feedbackEl.innerHTML = `
          <strong class="block text-slate-900 mb-0.5">Gabarito Comentado (Alternativa correta: ${q.resposta_correta}):</strong>
          <span>${q.explicacao}</span>
        `;
      }
    });

    const boxPlacar = document.getElementById('box-pontuacao');
    const valorPlacar = document.getElementById('pontos-valor');
    if (boxPlacar && valorPlacar) {
      valorPlacar.textContent = acertos;
      boxPlacar.classList.remove('hidden');
    }
  }

  toggleRespostaEsperada(id) {
    const el = document.getElementById(`resp-disc-${id}`);
    if (el) {
      el.classList.toggle('hidden');
    }
  }

  exportarMarkdown() {
    if (!this.currentData) {
      alert("Nenhum dado gerado para exportar.");
      return;
    }
    const d = this.currentData;
    let md = `# Plano de Estudos e Simulado Acadêmico\n`;
    md += `**Disciplina:** ${d.disciplina}\n`;
    md += `**Tempo até a prova:** ${d.dias_ate_prova} dias (${d.horas_por_dia}h/dia)\n\n`;
    
    md += `## 1. Resumo Estruturado\n${d.resumo.visao_geral}\n\n`;
    d.resumo.topicos.forEach(t => {
      md += `### ${t.nome} [Complexidade: ${t.complexidade}]\n`;
      md += `${t.definicao}\n`;
      (t.pontos_criticos || []).forEach(p => md += `- ${p}\n`);
      md += `\n`;
    });

    md += `## 2. Simulado da Banca\n`;
    d.simulado.questoes_multipla_escolha.forEach((q, idx) => {
      md += `**Questão ${idx + 1}:** ${q.enunciado}\n`;
      for (const [letra, txt] of Object.entries(q.alternativas)) {
        md += `- (${letra}) ${txt}\n`;
      }
      md += `*Gabarito:* ${q.resposta_correta} - ${q.explicacao}\n\n`;
    });

    md += `## 3. Cronograma de Revisão Espaçada\n`;
    d.cronograma.dias.forEach(dia => {
      md += `### Dia ${dia.dia}: ${dia.foco_principal} (${dia.horas_previstas}h)\n`;
      (dia.atividades || []).forEach(a => md += `- ${a}\n`);
      md += `\n`;
    });

    const blob = new Blob([md], {type: 'text/markdown;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `plano_estudos_${Date.now()}.md`;
    link.click();
  }
}

// Inicializa a aplicação quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
  window.app = new StudyApp();
});
