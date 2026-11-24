import json
import logging
import os
import threading
from typing import Dict, Any, Callable, Optional
from backend.services.demo_data import DEMO_DATA
from backend.services.llm_factory import get_llm_instance

logger = logging.getLogger(__name__)

# Processa um material por vez: evita que execuções simultâneas estourem o
# limite de requisições por minuto do plano gratuito do Gemini.
_crew_lock = threading.Lock()

# Regra extra para os agentes: símbolos em LaTeX (\forall, \in...) quebram o JSON
REGRA_JSON = (
    "\nIMPORTANTE: responda somente com o JSON, sem texto antes ou depois. "
    "Não use LaTeX nem barras invertidas; escreva símbolos matemáticos "
    "diretamente em Unicode (ex.: ∀, ∃, ∈, ≠, ≤, ⇒)."
)


def clean_json_output(raw_text: str) -> Dict[str, Any]:
    """Converte a resposta do agente em dict, tolerando markdown e JSON malformado."""
    text = raw_text.strip()
    # Remove cercas ```json ... ``` e qualquer texto fora do objeto JSON
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        text = text[start:end + 1]

    try:
        # strict=False aceita quebras de linha literais dentro das strings
        return json.loads(text, strict=False)
    except json.JSONDecodeError as err:
        logger.warning(f"JSON inválido do agente ({err}); tentando reparar.")

    # Repara barras invertidas soltas, vírgulas sobrando, aspas faltando etc.
    from json_repair import repair_json
    reparado = repair_json(text, return_objects=True)
    if isinstance(reparado, dict) and reparado:
        return reparado
    logger.error(f"Não foi possível reparar o JSON do agente. Texto bruto: {raw_text[:2000]}")
    raise ValueError("Resposta do agente não é um JSON válido.")

def run_study_crew(
    texto_material: str,
    disciplina: str,
    dias_ate_prova: int,
    horas_por_dia: float,
    num_questoes: int = 5,
    provider: str = "demo",
    model_name: Optional[str] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Dict[str, Any]:
    """
    Executa o fluxo multiagente sequencial com 3 agentes especializados:
    1. Agente 1 - Sintetizador Acadêmico
    2. Agente 2 - Elaborador de Banca Examinadora
    3. Agente 3 - Tutor de Revisão Espaçada
    """
    # O simulado tem entre 5 e 10 questões objetivas
    num_questoes = max(5, min(10, int(num_questoes or 5)))

    if provider.lower() == "demo":
        if progress_callback:
            progress_callback(1, "1. Sintetizando conteúdo acadêmico (Modo Demonstração Instantâneo)...")
            progress_callback(2, "2. Elaborando questões de banca examinadora e gabarito comentado...")
            progress_callback(3, "3. Organizando cronograma otimizado de revisão espaçada...")
        
        # Cria uma cópia com os dados fornecidos pelo usuário
        result = dict(DEMO_DATA)
        result["disciplina"] = disciplina or DEMO_DATA["disciplina"]
        result["dias_ate_prova"] = dias_ate_prova or DEMO_DATA["dias_ate_prova"]
        result["horas_por_dia"] = horas_por_dia or DEMO_DATA["horas_por_dia"]
        simulado_demo = dict(DEMO_DATA["simulado"])
        simulado_demo["questoes_multipla_escolha"] = DEMO_DATA["simulado"]["questoes_multipla_escolha"][:num_questoes]
        result["simulado"] = simulado_demo
        return result

    # Configura LLM real para CrewAI
    llm = get_llm_instance(provider=provider, model_name=model_name)
    
    from crewai import Agent, Task, Crew, Process

    # Notificação do Agente 1
    if progress_callback:
        progress_callback(1, "1. Sintetizador Acadêmico extraindo conceitos e classificando complexidade...")

    agente_sintetizador = Agent(
        role="Especialista em Didática e Extração de Conhecimento Acadêmico",
        goal=f"Analisar o material da disciplina '{disciplina}', extrair tópicos fundamentais, regras/fórmulas e classificar cada um por complexidade (Baixa, Média ou Alta). Responder estritamente em Português (PT-BR).",
        backstory=(
            "Você é um professor titular e pedagogo sênior renomado com vasta experiência em condensar "
            "materiais densos em sínteses conceituais claras, identificando com precisão o que é essencial "
            "para o domínio do estudante e classificando a complexidade de cada tema."
        ),
        llm=llm,
        verbose=True
    )

    tarefa_sintese = Task(
        description=(
            f"Analise estritamente o conteúdo fornecido a seguir da disciplina '{disciplina}'.\n\n"
            f"CONTEÚDO:\n{texto_material[:12000]}\n\n"
            "Gere uma síntese em formato JSON estruturado com a seguinte chave raiz 'resumo':\n"
            "{\n"
            '  "titulo": "Título do resumo",\n'
            '  "visao_geral": "Parágrafo com a visão geral do conteúdo",\n'
            '  "topicos": [\n'
            '    {\n'
            '      "nome": "Nome do tópico",\n'
            '      "complexidade": "Baixa" | "Média" | "Alta",\n'
            '      "definicao": "Definição formal e didática",\n'
            '      "pontos_criticos": ["Ponto crítico 1", "Ponto crítico 2"]\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "Responda estritamente com o JSON válido, sem comentários adicionais."
            + REGRA_JSON
        ),
        expected_output="JSON estruturado contendo 'resumo' com titulo, visao_geral e lista de topicos classificados.",
        agent=agente_sintetizador
    )

    # Agente 2: Elaborador de Banca Examinadora
    agente_banca = Agent(
        role="Professor Universitário e Projetista de Avaliações Acadêmicas",
        goal=f"Criar um simulado avaliativo rigoroso e inédito para a disciplina '{disciplina}', contendo {num_questoes} questões objetivas com 4 alternativas (A, B, C, D) e gabarito comentado fundamentado no resumo.",
        backstory=(
            "Você é o presidente da banca de elaboração de provas da universidade. Seu rigor na construção "
            "de enunciados contextualizados, distratores plausíveis e gabaritos comentados esclarecedores "
            "é referência para avaliar a real compreensão dos alunos."
        ),
        llm=llm,
        verbose=True
    )

    tarefa_simulado = Task(
        description=(
            "Com base no resumo estruturado gerado pelo Agente 1, elabore um simulado inédito contendo:\n"
            f"- EXATAMENTE {num_questoes} questões de múltipla escolha, nem mais nem menos (alternativas A, B, C, D) com enunciado contextualizado, identificação da alternativa correta e explicação detalhada da justificativa da correta e do erro dos distratores.\n"
            "- NÃO inclua questões discursivas: o simulado é composto somente pelas questões objetivas.\n\n"
            "Gere a saída estritamente em formato JSON estruturado sob a chave 'simulado':\n"
            "{\n"
            '  "questoes_multipla_escolha": [\n'
            '    {\n'
            '      "id": 1,\n'
            '      "enunciado": "...",\n'
            '      "alternativas": {"A": "...", "B": "...", "C": "...", "D": "..."},\n'
            '      "resposta_correta": "A" | "B" | "C" | "D",\n'
            '      "explicacao": "..."\n'
            '    }\n'
            '  ]\n'
            "}\n"
            f"A lista 'questoes_multipla_escolha' deve ter exatamente {num_questoes} itens. "
            "Responda estritamente com o JSON válido."
            + REGRA_JSON
        ),
        expected_output=f"JSON estruturado contendo 'simulado' com as {num_questoes} questões objetivas gabaritadas.",
        agent=agente_banca
    )

    # Agente 3: Tutor de Revisão Espaçada
    agente_tutor = Agent(
        role="Estrategista de Aprendizagem e Gestão de Tempo de Estudos",
        goal=f"Construir um cronograma dia a dia personalizado para os {dias_ate_prova} dias restantes, dedicando {horas_por_dia}h/dia, priorizando tópicos de Alta complexidade e intercalando revisão ativa.",
        backstory=(
            "Você é um cientista cognitivo especializado na curva do esquecimento de Ebbinghaus e na técnica "
            "de repetição espaçada. Você monta cronogramas pragmáticos que maximizam a retenção e a prática ativa "
            "respeitando a disponibilidade diária de horas do estudante."
        ),
        llm=llm,
        verbose=True
    )

    tarefa_cronograma = Task(
        description=(
            f"Com base nos tópicos identificados e na complexidade indicada pelo Agente 1, monte um cronograma de estudos para {dias_ate_prova} dias, com meta de {horas_por_dia} horas por dia.\n"
            "Regras obrigatórias:\n"
            "- Priorize os tópicos de complexidade Alta nos primeiros dias para permitir repetição espaçada.\n"
            "- Inclua momentos explícitos de prática ativa (resolver simulado e redigir respostas).\n"
            "- O último dia deve ser focado em revisão de distratores e consolidação.\n\n"
            "Gere a saída estritamente em formato JSON estruturado sob a chave 'cronograma':\n"
            "{\n"
            '  "resumo_estrategia": "Explicação pedagógica da divisão dos dias",\n'
            '  "dias": [\n'
            '    {\n'
            '      "dia": 1,\n'
            '      "horas_previstas": ' + str(horas_por_dia) + ',\n'
            '      "foco_principal": "Tema central do dia",\n'
            '      "topicos_alvo": ["Tópico 1", "Tópico 2"],\n'
            '      "atividades": ["Atividade detalhada 1 com duração sugerida", "Atividade 2"]\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "Responda estritamente com o JSON válido."
            + REGRA_JSON
        ),
        expected_output="JSON estruturado contendo 'cronograma' detalhando cada dia até a prova.",
        agent=agente_tutor
    )

    # Limite de chamadas por minuto ao LLM (plano gratuito do Gemini: 5/min)
    max_rpm = int(os.getenv("LLM_MAX_RPM", "4")) if provider.lower() == "gemini" else None

    # Execução sequencial da Crew
    crew = Crew(
        agents=[agente_sintetizador, agente_banca, agente_tutor],
        tasks=[tarefa_sintese, tarefa_simulado, tarefa_cronograma],
        process=Process.sequential,
        max_rpm=max_rpm,
        verbose=True
    )

    with _crew_lock:
        crew.kickoff()

    # A saída final da Crew contém só a última tarefa (cronograma).
    # Por isso consolidamos o JSON de cada uma das 3 tarefas individualmente.
    # O LLM às vezes omite a chave raiz ('resumo', 'simulado', 'cronograma'):
    # nesse caso o JSON inteiro é encaixado na chave esperada da tarefa.
    parsed_result = {}
    for chave, task in (("resumo", tarefa_sintese), ("simulado", tarefa_simulado), ("cronograma", tarefa_cronograma)):
        raw = getattr(task.output, "raw", None) or str(task.output)
        try:
            task_json = clean_json_output(raw)
            if isinstance(task_json, dict) and chave in task_json:
                parsed_result[chave] = task_json[chave]
            elif isinstance(task_json, dict) and task_json:
                parsed_result[chave] = task_json
        except Exception as task_err:
            logger.error(f"Erro ao extrair JSON da tarefa '{chave}': {task_err}")

    # Sem dados de demonstração no lugar do resultado real: se algum agente
    # não devolveu JSON válido, avisa o usuário em vez de mostrar conteúdo falso.
    faltando = [chave for chave in ("resumo", "simulado", "cronograma") if chave not in parsed_result]
    if faltando:
        nomes = {"resumo": "resumo", "simulado": "simulado", "cronograma": "cronograma"}
        raise ValueError(
            "Os agentes não retornaram uma resposta válida para: "
            + ", ".join(nomes[c] for c in faltando)
            + ". Tente processar novamente."
        )

    # Garante o número de questões escolhido pelo usuário
    simulado = parsed_result["simulado"]
    objetivas = simulado.get("questoes_multipla_escolha") or []
    if len(objetivas) != num_questoes:
        logger.warning(f"Agente gerou {len(objetivas)} questões objetivas; solicitadas: {num_questoes}.")
    simulado["questoes_multipla_escolha"] = objetivas[:num_questoes]
    simulado.pop("questoes_discursivas", None)

    final_output = {
        "disciplina": disciplina,
        "dias_ate_prova": dias_ate_prova,
        "horas_por_dia": horas_por_dia,
        "resumo": parsed_result["resumo"],
        "simulado": parsed_result["simulado"],
        "cronograma": parsed_result["cronograma"],
    }
    return final_output
