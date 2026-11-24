/**
 * Gestor Inteligente de Estudos e Simulador de Provas Multiagentes
 */

const ALT_BASE = "flex items-start space-x-2.5 p-3 rounded border text-sm";

function esc(valor) {
  return String(valor ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

class StudyApp {
  constructor() {
    this.currentData = null;
    this.tipoEntrada = 'pdf'; // 'pdf' | 'text'
    this.respostasUsuario = {};
    // O sistema sempre abre no Google Gemini
    this.providerAtual = 'gemini';
    document.getElementById('provider-select').value = this.providerAtual;
    this.configurarArrastarSoltar();
  }

  mudarProvedor(val) {
    this.providerAtual = val;
  }

  configurarArrastarSoltar() {
    const area = document.getElementById('area-upload-pdf');
    const input = document.getElementById('arquivo-pdf');
    ['dragenter', 'dragover'].forEach(evt => area.addEventListener(evt, e => {
      e.preventDefault();
      area.classList.add('border-slate-500');
    }));
    ['dragleave', 'drop'].forEach(evt => area.addEventListener(evt, e => {
      e.preventDefault();
      area.classList.remove('border-slate-500');
    }));
    area.addEventListener('drop', e => {
      const arquivo = e.dataTransfer.files && e.dataTransfer.files[0];
      if (!arquivo) return;
      if (!arquivo.name.toLowerCase().endsWith('.pdf')) {
        alert('Somente arquivos PDF são aceitos.');
        return;
      }
      const dt = new DataTransfer();
      dt.items.add(arquivo);
      input.files = dt.files;
      this.atualizarNomeArquivo(input);
    });
  }

  selecionarAbaEntrada(tipo) {
    this.tipoEntrada = tipo;
    const btnPdf = document.getElementById('tab-btn-pdf');
    const btnText = document.getElementById('tab-btn-text');
    const areaPdf = document.getElementById('area-upload-pdf');
    const areaText = document.getElementById('area-colar-texto');
    const ativo = "text-[11px] px-2 py-0.5 rounded font-medium bg-slate-900 text-white";
    const inativo = "text-[11px] px-2 py-0.5 rounded font-medium text-slate-600 hover:bg-slate-100";

    btnPdf.className = tipo === 'pdf' ? ativo : inativo;
    btnText.className = tipo === 'pdf' ? inativo : ativo;
    areaPdf.classList.toggle('hidden', tipo !== 'pdf');
    areaText.classList.toggle('hidden', tipo === 'pdf');
  }

  atualizarNomeArquivo(input) {
    const label = document.getElementById('label-arquivo');
    if (input.files && input.files[0]) {
      label.textContent = `Arquivo selecionado: ${input.files[0].name} (${(input.files[0].size / 1024).toFixed(1)} KB)`;
    } else {
      label.textContent = "Clique ou arraste um arquivo PDF aqui";
    }
  }

  mudarAbaResultado(aba) {
    ['resumo', 'simulado', 'cronograma'].forEach(nome => {
      const elConteudo = document.getElementById(`conteudo-${nome}`);
      const elNav = document.getElementById(`tab-nav-${nome}`);
      if (nome === aba) {
        elConteudo.classList.remove('hidden');
        elNav.className = "py-3 px-1 border-b-2 border-[#1E3A8A] font-semibold text-xs text-[#1E3A8A] flex items-center space-x-1.5 whitespace-nowrap";
      } else {
        elConteudo.classList.add('hidden');
        elNav.className = "py-3 px-1 border-b-2 border-transparent font-medium text-xs text-slate-500 hover:text-slate-800 hover:border-slate-300 flex items-center space-x-1.5 whitespace-nowrap";
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
    const numQuestoes = parseInt(document.getElementById('num-questoes').value) || 5;

    let fileInput = null;
    let texto = '';
    if (this.tipoEntrada === 'pdf') {
      fileInput = document.getElementById('arquivo-pdf');
      if (!fileInput.files || !fileInput.files[0]) {
        alert("Por favor, selecione um arquivo PDF.");
        return;
      }
    } else {
      texto = document.getElementById('texto-material').value;
      if (!texto.trim()) {
        alert("Por favor, cole o texto do material.");
        return;
      }
    }

    btnSubmit.disabled = true;
    btnSubmit.classList.add('opacity-50', 'cursor-not-allowed');
    boxProgresso.classList.remove('hidden');
    barra.style.width = '20%';
    statusTxt.textContent = "Iniciando Agente 1 (Sintetizador)...";

    // O processamento com o Gemini leva de 30s a alguns minutos: mostra o tempo decorrido
    const inicio = Date.now();
    const timer = setInterval(() => {
      const seg = Math.round((Date.now() - inicio) / 1000);
      const largura = Math.min(90, 20 + seg * 0.6);
      barra.style.width = largura + '%';
      let etapa = "Agente 1 (Sintetizador) analisando o material";
      if (largura > 45) etapa = "Agente 2 (Banca Examinadora) elaborando questões";
      if (largura > 70) etapa = "Agente 3 (Tutor Espaçado) construindo cronograma";
      statusTxt.textContent = `${etapa}... ${seg}s (pode levar alguns minutos)`;
    }, 1000);

    try {
      let resp;
      if (this.tipoEntrada === 'pdf') {
        const formData = new FormData();
        formData.append('disciplina', disciplina);
        formData.append('dias_ate_prova', dias);
        formData.append('horas_por_dia', horas);
        formData.append('num_questoes', numQuestoes);
        formData.append('provider', this.providerAtual);
        formData.append('arquivo', fileInput.files[0]);
        resp = await fetch('/api/processar-pdf', { method: 'POST', body: formData });
      } else {
        resp = await fetch('/api/processar-texto', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            disciplina: disciplina,
            dias_ate_prova: dias,
            horas_por_dia: horas,
            num_questoes: numQuestoes,
            texto_material: texto,
            provider: this.providerAtual
          })
        });
      }

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || "Erro ao processar o material");
      }
      const data = await resp.json();

      clearInterval(timer);
      barra.style.width = '100%';
      statusTxt.textContent = "Orquestração concluída!";
      setTimeout(() => {
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

    const area = document.getElementById('area-resultados');
    area.classList.remove('hidden');
    area.classList.add('flex');
    this.mudarAbaResultado('resumo');

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
        <li class="flex items-start space-x-1.5 text-sm text-slate-600">
          <span class="text-slate-400">&bull;</span>
          <span>${esc(p)}</span>
        </li>
      `).join('');

      const card = document.createElement('div');
      card.className = "border border-slate-200 rounded p-4 bg-slate-50/50 space-y-2";
      card.innerHTML = `
        <div class="flex items-center justify-between gap-2">
          <h5 class="text-sm font-semibold text-slate-900">${esc(t.nome)}</h5>
          <span class="text-[10px] font-semibold px-2 py-0.5 rounded border whitespace-nowrap ${badgeClass}">
            Complexidade ${esc(t.complexidade)}
          </span>
        </div>
        <p class="text-sm text-slate-600 leading-relaxed">${esc(t.definicao)}</p>
        <ul class="space-y-1 pt-1 border-t border-slate-200/60">
          ${pontosHtml}
        </ul>
      `;
      listaTopicosEl.appendChild(card);
    });

    // 2. Simulado
    const simulado = data.simulado || {};
    const questoesObj = simulado.questoes_multipla_escolha || [];
    const questoesDisc = simulado.questoes_discursivas || [];
    const containerObj = document.getElementById('lista-questoes-objetivas');
    containerObj.innerHTML = '';
    document.getElementById('box-pontuacao').classList.add('hidden');
    document.getElementById('pontos-total').textContent = questoesObj.length;
    document.getElementById('badge-simulado').textContent = `${questoesObj.length + questoesDisc.length} Qs`;
    document.getElementById('simulado-descricao').textContent =
      `${questoesObj.length} questões objetivas com correção automática + ${questoesDisc.length} questões discursivas.`;

    questoesObj.forEach((q, idx) => {
      const qDiv = document.createElement('div');
      qDiv.className = "border border-slate-200 rounded-lg p-5 bg-white shadow-sm space-y-3";

      let alternativasHtml = '';
      for (const [letra, texto] of Object.entries(q.alternativas || {})) {
        alternativasHtml += `
          <label class="${ALT_BASE} border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors text-slate-700" id="alt-box-${idx}-${esc(letra)}">
            <input type="radio" name="questao-${idx}" value="${esc(letra)}" onchange="window.app.selecionarResposta(${idx}, this.value)" class="mt-1 text-[#1E3A8A] focus:ring-0">
            <span class="font-semibold text-slate-900">${esc(letra)})</span>
            <span class="leading-relaxed">${esc(texto)}</span>
          </label>
        `;
      }

      qDiv.innerHTML = `
        <div class="flex items-start justify-between">
          <span class="text-sm font-bold text-[#1E3A8A]">Questão ${idx + 1} (Objetiva)</span>
          <span id="q-status-${idx}" class="text-xs font-medium text-slate-400">Não respondida</span>
        </div>
        <p class="text-base text-slate-800 leading-relaxed font-medium">${esc(q.enunciado)}</p>
        <div class="space-y-2 pt-1">
          ${alternativasHtml}
        </div>
        <div id="q-feedback-${idx}" class="hidden"></div>
      `;
      containerObj.appendChild(qDiv);
    });

    const containerDisc = document.getElementById('lista-questoes-discursivas');
    containerDisc.innerHTML = '';

    questoesDisc.forEach((qd, idx) => {
      const discDiv = document.createElement('div');
      discDiv.className = "border border-slate-200 rounded-lg p-5 bg-white shadow-sm space-y-3";
      discDiv.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="text-sm font-bold text-slate-800">Questão Discursiva ${idx + 1}</span>
          <button onclick="window.app.toggleRespostaEsperada(${idx})" class="text-sm text-[#1E3A8A] hover:underline font-medium">
            Ver resposta esperada
          </button>
        </div>
        <p class="text-base text-slate-800 leading-relaxed font-medium">${esc(qd.enunciado)}</p>
        <textarea rows="3" placeholder="Redija seu rascunho de resposta aqui para fixação..."
          class="w-full text-sm p-3 border border-slate-200 rounded focus:border-slate-800 focus:outline-none"></textarea>
        <div id="resp-disc-${idx}" class="hidden p-3 bg-slate-50 border border-slate-200 rounded text-sm text-slate-700 whitespace-pre-line leading-relaxed">
          <strong class="block text-slate-900 mb-1">Gabarito Conceitual do Professor:</strong>${esc(qd.resposta_esperada)}
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
        <li class="flex items-start space-x-2 text-sm text-slate-700">
          <span class="text-[#1E3A8A] font-bold">&bull;</span>
          <span>${esc(a)}</span>
        </li>
      `).join('');

      const topicosBadges = (d.topicos_alvo || []).map(t => `
        <span class="inline-block text-[10px] bg-slate-100 text-slate-700 border border-slate-200 px-1.5 py-0.5 rounded">${esc(t)}</span>
      `).join(' ');

      const diaCard = document.createElement('div');
      diaCard.className = "border border-slate-200 rounded-lg p-4 bg-white shadow-sm space-y-2";
      diaCard.innerHTML = `
        <div class="flex items-center justify-between gap-2 border-b border-slate-100 pb-2">
          <div class="flex items-center space-x-2">
            <span class="bg-[#1E3A8A] text-white text-[11px] font-bold px-2 py-0.5 rounded whitespace-nowrap">Dia ${esc(d.dia)}</span>
            <h5 class="text-sm font-semibold text-slate-900">${esc(d.foco_principal)}</h5>
          </div>
          <span class="text-xs font-mono text-slate-500 whitespace-nowrap">${esc(d.horas_previstas)}h de estudo</span>
        </div>
        <div class="pt-1">
          <div class="text-[11px] text-slate-500 mb-1.5">Tópicos priorizados: ${topicosBadges}</div>
          <ul class="space-y-1.5">${ativHtml}</ul>
        </div>
      `;
      containerDias.appendChild(diaCard);
    });

    area.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  selecionarResposta(idx, letra) {
    this.respostasUsuario[idx] = letra;
    const statusEl = document.getElementById(`q-status-${idx}`);
    if (statusEl) {
      statusEl.textContent = `Marcada: ${letra}`;
      statusEl.className = "text-xs font-semibold text-slate-700";
    }
  }

  corrigirSimulado() {
    if (!this.currentData || !this.currentData.simulado) return;
    const questoes = this.currentData.simulado.questoes_multipla_escolha || [];
    let acertos = 0;

    questoes.forEach((q, idx) => {
      const respUser = this.respostasUsuario[idx];
      const feedbackEl = document.getElementById(`q-feedback-${idx}`);
      const statusEl = document.getElementById(`q-status-${idx}`);

      for (const letra of Object.keys(q.alternativas || {})) {
        const altBox = document.getElementById(`alt-box-${idx}-${letra}`);
        if (altBox) altBox.className = `${ALT_BASE} border-slate-200 text-slate-700`;
      }

      const correta = respUser === q.resposta_correta;
      if (correta) acertos++;
      if (statusEl) {
        statusEl.textContent = correta ? "✓ Correta" : "✕ Incorreta";
        statusEl.className = `text-xs font-semibold ${correta ? 'text-emerald-700' : 'text-red-600'}`;
      }

      const boxCorreta = document.getElementById(`alt-box-${idx}-${q.resposta_correta}`);
      if (boxCorreta) {
        boxCorreta.className = `${ALT_BASE} border-emerald-300 bg-emerald-50 text-emerald-900 font-medium`;
      }
      if (respUser && !correta) {
        const boxErrada = document.getElementById(`alt-box-${idx}-${respUser}`);
        if (boxErrada) boxErrada.className = `${ALT_BASE} border-red-300 bg-red-50 text-red-900`;
      }

      if (feedbackEl) {
        feedbackEl.className = "p-3 rounded border text-sm leading-relaxed mt-2 bg-slate-50 border-slate-200 text-slate-800";
        feedbackEl.innerHTML = `
          <strong class="block text-slate-900 mb-0.5">Gabarito Comentado (Alternativa correta: ${esc(q.resposta_correta)}):</strong>
          <span>${esc(q.explicacao)}</span>
        `;
      }
    });

    document.getElementById('pontos-valor').textContent = acertos;
    document.getElementById('box-pontuacao').classList.remove('hidden');
  }

  toggleRespostaEsperada(idx) {
    const el = document.getElementById(`resp-disc-${idx}`);
    if (el) el.classList.toggle('hidden');
  }

  montarHtmlPdf() {
    const d = this.currentData;
    const resumo = d.resumo || {};
    const simulado = d.simulado || {};
    const cronograma = d.cronograma || {};
    const h2 = 'font-size:16px;color:#1E3A8A;border-bottom:1px solid #CBD5E1;padding-bottom:4px;margin:22px 0 10px;';
    const bloco = 'page-break-inside:avoid;margin-bottom:12px;';

    const topicos = (resumo.topicos || []).map(t => `
      <div style="${bloco}">
        <div style="font-weight:600;font-size:13px;">${esc(t.nome)} <span style="font-weight:400;color:#64748B;">(Complexidade ${esc(t.complexidade)})</span></div>
        <div style="font-size:12px;margin:3px 0;">${esc(t.definicao)}</div>
        ${(t.pontos_criticos || []).map(p => `<div style="font-size:12px;color:#334155;margin:1px 0 1px 10px;">• ${esc(p)}</div>`).join('')}
      </div>`).join('');

    const objetivas = (simulado.questoes_multipla_escolha || []).map((q, i) => `
      <div style="${bloco}">
        <div style="font-weight:600;font-size:13px;">Questão ${i + 1}</div>
        <div style="font-size:13px;margin:3px 0 5px;">${esc(q.enunciado)}</div>
        ${Object.entries(q.alternativas || {}).map(([l, t]) => `<div style="font-size:12px;margin:2px 0 2px 10px;"><b>${esc(l)})</b> ${esc(t)}</div>`).join('')}
      </div>`).join('');

    const discursivas = (simulado.questoes_discursivas || []).map((q, i) => `
      <div style="${bloco}">
        <div style="font-weight:600;font-size:13px;">Questão Discursiva ${i + 1}</div>
        <div style="font-size:13px;margin-top:3px;">${esc(q.enunciado)}</div>
      </div>`).join('');

    const gabarito = (simulado.questoes_multipla_escolha || []).map((q, i) => `
      <div style="${bloco}font-size:12px;"><b>Questão ${i + 1}: ${esc(q.resposta_correta)}</b> — ${esc(q.explicacao)}</div>`).join('')
      + (simulado.questoes_discursivas || []).map((q, i) => `
      <div style="${bloco}font-size:12px;white-space:pre-line;"><b>Discursiva ${i + 1}:</b> ${esc(q.resposta_esperada)}</div>`).join('');

    const dias = (cronograma.dias || []).map(dia => `
      <div style="${bloco}">
        <div style="font-weight:600;font-size:13px;">Dia ${esc(dia.dia)}: ${esc(dia.foco_principal)} <span style="font-weight:400;color:#64748B;">(${esc(dia.horas_previstas)}h)</span></div>
        ${(dia.atividades || []).map(a => `<div style="font-size:12px;margin:2px 0 2px 10px;">• ${esc(a)}</div>`).join('')}
      </div>`).join('');

    return `
      <div style="font-family:Inter,Arial,sans-serif;color:#0F172A;padding:4px;">
        <div style="font-size:20px;font-weight:700;">Plano de Estudos e Simulado</div>
        <div style="font-size:12px;color:#475569;margin-top:4px;">
          Disciplina: ${esc(d.disciplina)} · ${esc(d.dias_ate_prova)} dias até a prova · ${esc(d.horas_por_dia)}h por dia
        </div>
        <h2 style="${h2}">1. Resumo Estruturado</h2>
        <div style="font-weight:600;font-size:14px;">${esc(resumo.titulo)}</div>
        <div style="font-size:12px;margin:4px 0 12px;">${esc(resumo.visao_geral)}</div>
        ${topicos}
        <h2 style="${h2}">2. Simulado</h2>
        ${objetivas}
        ${discursivas}
        <h2 style="${h2}">3. Gabarito Comentado</h2>
        ${gabarito}
        <h2 style="${h2}">4. Cronograma de Estudos</h2>
        <div style="font-size:12px;margin-bottom:10px;">${esc(cronograma.resumo_estrategia)}</div>
        ${dias}
      </div>`;
  }

  async baixarPdf() {
    if (!this.currentData) {
      alert("Nenhum resultado gerado para baixar.");
      return;
    }
    if (typeof html2pdf === 'undefined') {
      alert("Não foi possível carregar o gerador de PDF. Verifique a conexão com a internet.");
      return;
    }
    const btn = document.getElementById('btn-download');
    btn.disabled = true;
    btn.textContent = 'Gerando PDF...';
    try {
      const nome = (this.currentData.disciplina || 'plano_estudos')
        .normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_|_$/g, '').toLowerCase();
      await html2pdf().set({
        margin: [12, 12, 14, 12],
        filename: `${nome || 'plano_estudos'}.pdf`,
        image: { type: 'jpeg', quality: 0.95 },
        // scrollX/scrollY = 0 evita espaço em branco no topo quando a página está rolada
        html2canvas: { scale: 2, scrollX: 0, scrollY: 0 },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['css', 'legacy'] }
      }).from(this.montarHtmlPdf()).save();
    } catch (e) {
      alert(`Falha ao gerar o PDF: ${e.message}`);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Download';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new StudyApp();
});
