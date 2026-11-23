import json
import logging
from typing import Dict, Any, Callable, Optional
from backend.services.demo_data import DEMO_DATA
from backend.services.llm_factory import get_llm_instance

logger = logging.getLogger(__name__)

def clean_json_output(raw_text: str) -> Dict[str, Any]:
    """Limpa blocos markdown ```json ... ``` caso a LLM retorne envolto em markdown."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        logger.error(f"Erro ao decodificar JSON gerado pelo agente: {err}\nTexto bruto: {raw_text}")
        # Tenta extrair a substring entre o primeiro { e o último }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
        raise err

def run_study_crew(
    texto_material: str,
    disciplina: str,
    dias_ate_prova: int,
    horas_por_dia: float,
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
        ),
        expected_output="JSON estruturado contendo 'resumo' com titulo, visao_geral e lista de topicos classificados.",
        agent=agente_sintetizador
    )

    # Agente 2: Elaborador de Banca Examinadora
    agente_banca = Agent(
        role="Professor Universitário e Projetista de Avaliações Acadêmicas",
        goal=f"Criar um simulado avaliativo rigoroso e inédito para a disciplina '{disciplina}', contendo 5 questões objetivas com 4 alternativas (A, B, C, D) e 2 questões discursivas com gabarito comentado fundamentado no resumo.",
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
            "- 5 questões de múltipla escolha (alternativas A, B, C, D) com enunciado contextualizado, identificação da alternativa correta e explicação detalhada da justificativa da correta e do erro dos distratores.\n"
            "- 2 questões discursivas conceituais com a 'resposta_esperada' completa do professor.\n\n"
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
            '  ],\n'
            '  "questoes_discursivas": [\n'
            '    {\n'
            '      "id": 1,\n'
            '      "enunciado": "...",\n'
            '      "resposta_esperada": "..."\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "Responda estritamente com o JSON válido."
        ),
        expected_output="JSON estruturado contendo 'simulado' com as 5 questões objetivas e 2 discursivas gabaritadas.",
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
        ),
        expected_output="JSON estruturado contendo 'cronograma' detalhando cada dia até a prova.",
        agent=agente_tutor
    )

    # Execução sequencial da Crew
    crew = Crew(
        agents=[agente_sintetizador, agente_banca, agente_tutor],
        tasks=[tarefa_sintese, tarefa_simulado, tarefa_cronograma],
        process=Process.sequential,
        verbose=True
    )

    crew_output = crew.kickoff()
    raw_result_str = str(crew_output)
    
    # Processa e consolida o JSON
    try:
        parsed_result = clean_json_output(raw_result_str)
    except Exception as e:
        logger.warning(f"Erro ao parsear saída final global da Crew: {e}. Coletando saídas individuais das tarefas...")
        parsed_result = {}
        for task in [tarefa_sintese, tarefa_simulado, tarefa_cronograma]:
            try:
                task_json = clean_json_output(str(task.output))
                parsed_result.update(task_json)
            except Exception as task_err:
                logger.error(f"Erro ao extrair JSON da tarefa individual: {task_err}")

    # Garante estrutura padronizada
    final_output = {
        "disciplina": disciplina,
        "dias_ate_prova": dias_ate_prova,
        "horas_por_dia": horas_por_dia,
        "resumo": parsed_result.get("resumo", DEMO_DATA["resumo"]),
        "simulado": parsed_result.get("simulado", DEMO_DATA["simulado"]),
        "cronograma": parsed_result.get("cronograma", DEMO_DATA["cronograma"]),
    }
    return final_output
