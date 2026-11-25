# Gestor Inteligente de Estudos e Simulador de Provas Baseado em Sistemas Multiagentes

Projeto acadêmico e prático desenvolvido para apresentação ao vivo no workshop da **FASOFT (Faculdade de Engenharia de Software - UniRV)**.

O sistema permite que visitantes, estudantes e professores enviem notas de aula, slides ou apostilas em formato **PDF** (ou colando o texto diretamente) e orquestra **3 agentes autônomos em sequência (CrewAI)** para produzir instantaneamente:
1. **Resumo Estruturado com Classificação de Complexidade Didática** (Baixa, Média, Alta);
2. **Simulado Avaliativo Interativo** (5 questões de múltipla escolha com correção automática e gabarito comentado + 2 questões discursivas);
3. **Cronograma Otimizado de Revisão Espaçada** baseado nos dias restantes até a prova e no tempo diário disponível do aluno.

---

## 🏛 Arquitetura do Sistema

```
                      ┌────────────────────────────────────────┐
                      │    Interface Web Acadêmica (PT-BR)     │
                      │ (Tailwind CSS Sóbrio / Design Humano)  │
                      └──────────────────┬─────────────────────┘
                                         │ Upload PDF / Texto
                                         ▼
                      ┌────────────────────────────────────────┐
                      │       FastAPI (Backend Python)         │
                      │    - Extrator PDF (pypdf)              │
                      │    - Seletor Híbrido de LLMs           │
                      └──────────────────┬─────────────────────┘
                                         │
             ┌───────────────────────────┴───────────────────────────┐
             ▼                                                       ▼
 ┌───────────────────────┐                               ┌───────────────────────┐
 │ Modo Nuvem / Online   │                               │ Modo Local / Offline  │
 │ - Google Gemini       │                               │ - Ollama Local        │
 │ - OpenAI (GPT-4o)     │                               │   (llama3.2 / qwen)   │
 └───────────────────────┘                               └───────────────────────┘
             ▲                                                       ▲
             └───────────────────────────┬───────────────────────────┘
                                         │
                     ┌───────────────────┴───────────────────┐
                     │     Pipeline Sequencial CrewAI        │
                     └───────────────────┬───────────────────┘
                                         │
      ┌──────────────────────────────────┼──────────────────────────────────┐
      ▼                                  ▼                                  ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│ Agente 1: Sintetizador    │ │ Agente 2: Banca Examinad. │ │ Agente 3: Tutor Espaçado  │
│ - Extração de conceitos   │ │ - 5 questões objetivas    │ │ - Cronograma dia a dia    │
│ - Regras e fórmulas       │ │ - 2 questões discursivas  │ │ - Foco em tópicos Alta C. │
│ - Nível de Complexidade   │ │ - Gabarito e correções    │ │ - Prática ativa           │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```

---

## 🚀 Como Executar no Windows (Execução em 1 Clique)

Para facilitar no dia do evento, basta dar um duplo-clique no arquivo:
```cmd
start.bat
```
O script configurará o ambiente virtual, as dependências e abrirá a aplicação em seu navegador em `http://localhost:8000`.

---

## ⚙️ Configuração Manual e Requisitos

### Pré-requisitos
- **Python 3.11 ou superior** instalado no computador.
- (Opcional para modo offline) **Ollama** instalado e rodando localmente (`http://localhost:11434`).

### Passo a Passo

1. **Clone ou abra o diretório do projeto:**
   ```bash
   cd N3
   ```

2. **Crie e ative um ambiente virtual Python:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```cmd
   pip install -r backend/requirements.txt
   ```

4. **Configuração de Variáveis de Ambiente (`.env`):**
   Crie ou edite o arquivo `backend/.env` (use `backend/.env.example` como modelo):
   ```env
   # Provedor padrão: 'demo', 'ollama', 'gemini' ou 'openai'
   LLM_PROVIDER=demo

   # Se for utilizar APIs em Nuvem no evento (caso haja internet estável):
   # Uma chave ou várias separadas por vírgula: se a cota de uma acabar,
   # o sistema passa para a próxima (cada chave de um projeto diferente do Google)
   GEMINI_API_KEY=sua_chave_gemini_aqui, outra_chave_opcional
   OPENAI_API_KEY=sua_chave_openai_aqui
   GEMINI_MODEL_NAME=gemini-1.5-flash
   OPENAI_MODEL_NAME=gpt-4o-mini

   # Se for utilizar contingência local 100% offline via Ollama:
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2
   ```

5. **Inicie o servidor:**
   ```cmd
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Acesse: `http://localhost:8000`

---

## 💡 Modos de Operação para o Workshop

O sistema conta com um **seletor no topo da tela** permitindo alternar de forma transparente:

1. **Modo Demonstração Instantâneo (Cache):**
   - Resposta imediata em menos de 1 segundo baseada em um caso real de *Engenharia de Software I (Arquitetura de Microsserviços e Pirâmide de Testes)*.
   - Ideal para apresentar a fluidez da interface para a banca ou professores sem depender de tempo de inferência de LLMs.

2. **Modo Contingência 100% Local / Offline (Ollama):**
   - Totalmente independente de internet.
   - Conecta ao serviço local do Ollama em `http://localhost:11434` (usando por exemplo `ollama run llama3.2` ou `qwen2.5:3b`).
   - Garante privacidade e imunidade a oscilações da rede Wi-Fi do auditório.
   - Como ativar:
     1. Instale o Ollama para Windows pelo site [ollama.com](https://ollama.com). Ele fica rodando em segundo plano na porta `11434`.
     2. Baixe o modelo usado pelo projeto: `ollama pull llama3.2`.
     3. No app, escolha **Ollama Local / Offline** no seletor do topo. Não é preciso reiniciar o servidor.
   - Para usar outro modelo (ex.: `qwen2.5:7b`, melhor em português, mas exige uns 16 GB de RAM), baixe-o com `ollama pull` e ajuste `OLLAMA_MODEL` no `backend/.env`.
   - Ao escolher o modo Ollama no seletor, o sistema já começa a carregar o modelo na memória e o mantém carregado por 30 minutos (`OLLAMA_KEEP_ALIVE` no `.env`). Por isso, escolha o modo alguns segundos antes de processar.
   - Roda inteiramente no computador, então é bem mais lento que o Gemini (pode levar alguns minutos sem placa de vídeo), e modelos pequenos às vezes devolvem respostas fora do formato esperado.

3. **Modo Nuvem (Google Gemini):**
   - Utiliza as APIs oficiais via chave configurada no `.env`.
   - Gera materiais ricos e aprofundados com alta fidelidade ao material didático anexado.

---

## 🎨 Diretrizes de Design Acadêmico

- **Estética Editorial e Limpa:** Tema 100% claro (`#FFFFFF` e `#F8FAFC`), bordas finas em ardósia (`#E2E8F0`) e tipografia moderna `Inter`.
- **Zero Distrações:** Sem degradês estridentes, sem sombras neon e sem elementos que remetam a robôs genéricos.
- **Interatividade Completa:** Quiz com seleção de alternativas em tempo real, cálculo de nota ao vivo e exportação em **Markdown** ou **Impressão PDF**.
