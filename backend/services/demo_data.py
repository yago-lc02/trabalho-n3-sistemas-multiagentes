DEMO_DATA = {
    "disciplina": "Engenharia de Software I - Arquitetura de Microsserviços e Testes",
    "dias_ate_prova": 5,
    "horas_por_dia": 2.5,
    "resumo": {
        "titulo": "Resumo Sintético: Arquitetura de Microsserviços e Qualidade de Software",
        "visao_geral": "O material aborda os princípios fundamentais da transição de monólitos para microsserviços, destacando padrões de comunicação síncrona/assíncrona, desacoplamento de banco de dados, governança descentralizada e a pirâmide de testes de software.",
        "topicos": [
            {
                "nome": "Decomposição de Monólitos e Padrão Strangler Fig",
                "complexidade": "Alta",
                "definicao": "Estratégia gradual de migração onde funcionalidades específicas do monólito são gradualmente substituídas por microsserviços independentes até a completa desativação do legado.",
                "pontos_criticos": [
                    "Evitar o 'Big Bang' na reescrita de sistemas legados",
                    "Uso de API Gateway / Reverse Proxy para roteamento seletivo de requisições",
                    "Garantia de consistência de dados durante o período de coexistência"
                ]
            },
            {
                "nome": "Comunicação Síncrona vs Assíncrona e Resiliência (Circuit Breaker)",
                "complexidade": "Alta",
                "definicao": "Padrões de integração entre serviços: chamadas HTTP/gRPC diretas (síncronas) vs mensageria/filas como Kafka e RabbitMQ (assíncronas), com aplicação do padrão Circuit Breaker para evitar falhas em cascata.",
                "pontos_criticos": [
                    "Três estados do Circuit Breaker: Fechado (normal), Aberto (falha rápida), Meio-Aberto (teste de recuperação)",
                    "Acoplamento temporal decorrente do excesso de chamadas síncronas",
                    "Uso de Timeouts agressivos e Fallbacks elegantes"
                ]
            },
            {
                "nome": "Database per Service e Consistência Eventual",
                "complexidade": "Alta",
                "definicao": "Cada microsserviço deve possuir e encapsular sua própria base de dados relacional ou NoSQL. Compartilhar bancos entre múltiplos serviços viola gravemente o isolamento.",
                "pontos_criticos": [
                    "Impossibilidade de transações ACID globais (Two-Phase Commit é custoso e frágil)",
                    "Aplicação do Padrão Saga (Orquestrada ou Coreografada) para transações distribuídas",
                    "Aceitação de Consistência Eventual no negócio"
                ]
            },
            {
                "nome": "Pirâmide de Testes e Estratégia de Qualidade",
                "complexidade": "Média",
                "definicao": "Hierarquia visual de tipos de testes proposta por Mike Cohn: base ampla de testes unitários rápidos e baratos, camada intermediária de testes de integração e topo estreito de testes ponta a ponta (E2E).",
                "pontos_criticos": [
                    "Testes Unitários: isolamento com Mocks e Stubs, cobertura de lógica de domínio pura",
                    "Testes de Contrato (ex: Pact) para garantir compatibilidade entre produtor e consumidor de APIs",
                    "Testes E2E: caros, lentos e suscetíveis a 'flakiness' (instabilidade temporária)"
                ]
            },
            {
                "nome": "Observabilidade e Rastreamento Distribuído (Distributed Tracing)",
                "complexidade": "Média",
                "definicao": "Capacidade de inferir o estado interno de um ecossistema distribuído a partir de seus três pilares: Logs Estruturados, Métricas de Telemetria e Traces de requisições entre serviços.",
                "pontos_criticos": [
                    "Propagação de Correlation ID (Trace ID e Span ID) nos headers HTTP",
                    "Padrão OpenTelemetry como padrão da indústria para coleta neutra de métricas"
                ]
            },
            {
                "nome": "Conceitos Básicos de Contêineres e Imutabilidade",
                "complexidade": "Baixa",
                "definicao": "Empacotamento de aplicações e todas as suas dependências em imagens Docker imutáveis para garantir reproducibilidade de execução entre ambientes.",
                "pontos_criticos": [
                    "Diferença entre Virtualização tradicional (Hypervisor) e Contêineres (compartilhamento do Kernel do SO)",
                    "Princípios de 12-Factor App (Twelve-Factor Methodology)"
                ]
            }
        ]
    },
    "simulado": {
        "questoes_multipla_escolha": [
            {
                "id": 1,
                "enunciado": "Em uma arquitetura de microsserviços, ao aplicar o padrão Circuit Breaker para mitigar falhas em cascata em um serviço de pagamentos com alta taxa de timeout, qual é o comportamento esperado quando o circuito atinge o estado 'Aberto' (Open)?",
                "alternativas": {
                    "A": "Todas as requisições recebidas continuam sendo encaminhadas ao serviço de destino com um timeout estendido para garantir a conclusão do processamento.",
                    "B": "As novas requisições falham imediatamente sem tentar invocar o serviço indisponível, retornando um erro rápido ou resposta de fallback pré-configurada.",
                    "C": "O circuito permite que exatamente 50% do tráfego passe para balancear a carga enquanto a equipe de infraestrutura reinicia os nós do serviço.",
                    "D": "O serviço armazena permanentemente em memória RAM todas as requisições acumuladas até que a dependência volte ao ar sem perda de transações."
                },
                "resposta_correta": "B",
                "explicacao": "No estado Aberto (Open), o Circuit Breaker interrompe o fluxo imediatamente ('fail-fast'), evitando sobrecarregar o serviço já instável e liberando recursos da aplicação cliente via fallback. No estado Meio-Aberto (Half-Open), um volume controlado de requisições teste é permitido para verificar a recuperação do serviço."
            },
            {
                "id": 2,
                "enunciado": "A decomposição de uma aplicação monolítica corporativa complexa frequentemente adota o Padrão Strangler Fig (Figueira Estranguladora). Qual é a principal premissa dessa abordagem de engenharia de software?",
                "alternativas": {
                    "A": "Reescrever todo o código-fonte legado em uma nova stack moderna em uma única etapa e realizar a virada de chave (Big Bang) no fim de semana.",
                    "B": "Interceptar chamadas nas bordas do sistema por meio de um proxy/gateway e substituir gradualmente módulos e rotas específicas por novos microsserviços até que o monólito seja extinto.",
                    "C": "Duplicar o banco de dados do monólito em réplicas de leitura e escrita sem alterar nenhuma linha da lógica de negócio monolítica.",
                    "D": "Encapsular o sistema monólito inteiro dentro de um contêiner Docker único e chamá-lo formalmente de microsserviço independente."
                },
                "resposta_correta": "B",
                "explicacao": "O Padrão Strangler Fig se baseia na migração incremental e de baixo risco, substituindo endpoints e fluxos específicos na borda (através de gateway) por novos serviços, reduzindo aos poucos o escopo do monólito até sua aposentadoria segura."
            },
            {
                "id": 3,
                "enunciado": "No contexto do padrão 'Database per Service', por que o compartilhamento de um banco de dados relacional comum entre múltiplos microsserviços é considerado um forte antipadrão de arquitetura?",
                "alternativas": {
                    "A": "Porque bancos relacionais são incapazes de armazenar dados serializados em JSON de requisições web modernas.",
                    "B": "Porque viola o encapsulamento e a autonomia dos serviços, acoplando esquemas de tabelas e impedindo deploys independentes das equipes.",
                    "C": "Porque bancos de dados SQL só aceitam conexões de um único endereço IP por determinação das especificações ISO da linguagem.",
                    "D": "Porque impossibilita a criação de índices e consultas com JOINs em tabelas internas do mesmo domínio."
                },
                "resposta_correta": "B",
                "explicacao": "Bancos compartilhados geram forte acoplamento no nível de esquema (schema). Se um serviço altera a coluna de uma tabela, pode quebrar silenciosamente outros serviços dependentes, destruindo a principal vantagem dos microsserviços: deploys independentes e autonomia de times."
            },
            {
                "id": 4,
                "enunciado": "Ao analisar a Pirâmide de Testes clássica proposta por Mike Cohn para assegurar a qualidade de um ecossistema de software, qual das alternativas descreve corretamente a proporção e o custo dos níveis de teste?",
                "alternativas": {
                    "A": "Os testes de ponta a ponta (E2E) devem compor a maior parte da suíte por testarem o sistema de forma mais realista e com menor custo de manutenção.",
                    "B": "A base deve ser composta prioritariamente por testes manuais de aceitação, garantindo que a percepção humana guie os testes de integração.",
                    "C": "A base deve ser maciça em testes unitários (rápidos, baratos e isolados), com camada intermediária de integração e um topo enxuto de testes ponta a ponta (E2E).",
                    "D": "Os testes de contrato substituem 100% a necessidade de testes de unidade e regras de negócio no código-fonte dos microsserviços."
                },
                "resposta_correta": "C",
                "explicacao": "A pirâmide preconiza ampla cobertura de testes unitários na base por serem determinísticos, velozes e de baixíssimo custo de infraestrutura. Testes E2E são lentos, frágeis e caros, devendo ser reservados para os fluxos mais críticos de ponta a ponta."
            },
            {
                "id": 5,
                "enunciado": "Para implementar observabilidade eficaz em uma malha de microsserviços onde uma única ação de usuário atravessa 8 serviços diferentes, qual mecanismo é fundamental para o Rastreamento Distribuído (Distributed Tracing)?",
                "alternativas": {
                    "A": "Configurar o mesmo arquivo de log físico em um compartilhamento de rede NFS para onde todos os containers escrevem simultaneamente.",
                    "B": "Propagar um identificador único de correlação (Correlation ID / Trace ID) nos cabeçalhos de cada requisição subsequente entre os serviços.",
                    "C": "Executar todos os microsserviços sob o mesmo processo no sistema operacional para compartilhar a memória global de logging.",
                    "D": "Desabilitar logs informativos e coletar apenas exceções fatais não tratadas na camada de infraestrutura."
                },
                "resposta_correta": "B",
                "explicacao": "O Trace ID (identificador de correlação) é propagado nos cabeçalhos HTTP/gRPC por toda a cadeia de chamadas, permitindo reunir em ferramentas como Jaeger ou Zipkin a linha do tempo exata de cada span de processamento através dos múltiplos nós da rede."
            }
        ]
    },
    "cronograma": {
        "resumo_estrategia": "Cronograma desenhado com foco em Revisão Espaçada e Prática Ativa. Os tópicos com maior densidade conceitual (Transações Distribuídas, Circuit Breaker e Strangler Fig) foram posicionados no início para permitir repetição espaçada e retenção de longo prazo antes da avaliação.",
        "dias": [
            {
                "dia": 1,
                "horas_previstas": 2.5,
                "foco_principal": "Arquitetura Fundamental e Decomposição de Monólitos",
                "topicos_alvo": [
                    "Decomposição de Monólitos e Padrão Strangler Fig",
                    "Database per Service e isolamento de esquemas"
                ],
                "atividades": [
                    "Leitura analítica dos conceitos de migração incremental e padrões de estrangulamento de monólitos (60 min)",
                    "Mapeamento conceitual do padrão Database per Service e análise de problemas de consistência (45 min)",
                    "Resolução das questões 2 e 3 do simulado interativo com anotação dos pontos de dúvida (45 min)"
                ]
            },
            {
                "dia": 2,
                "horas_previstas": 2.5,
                "foco_principal": "Resiliência e Comunicação entre Serviços",
                "topicos_alvo": [
                    "Comunicação Síncrona vs Assíncrona",
                    "Circuit Breaker (Estados: Closed, Open, Half-Open)"
                ],
                "atividades": [
                    "Estudo dos fluxos de falha em cascata e dimensionamento de Circuit Breaker (50 min)",
                    "Estudo das diferenças entre filas (RabbitMQ/Kafka) e chamadas RPC síncronas (50 min)",
                    "Revisão flashcard dos 3 estados do Circuit Breaker e resolução da questão 1 do simulado (50 min)"
                ]
            },
            {
                "dia": 3,
                "horas_previstas": 2.5,
                "foco_principal": "Transações Distribuídas e Revisão Prática",
                "topicos_alvo": [
                    "Padrão Saga (Orquestrada vs Coreografada)",
                    "Transações de Compensação e Consistência Eventual"
                ],
                "atividades": [
                    "Comparação técnica detalhada entre 2PC e Saga Pattern (60 min)",
                    "Revisão escrita sobre 2PC versus Padrão Saga sem consulta prévia (45 min)",
                    "Comparação da resposta redigida com a resposta esperada oficial e ajuste dos pontos fracos (45 min)"
                ]
            },
            {
                "dia": 4,
                "horas_previstas": 2.5,
                "foco_principal": "Qualidade de Software, Testes e Observabilidade",
                "topicos_alvo": [
                    "Pirâmide de Testes e Testes de Contrato (Pact)",
                    "Distributed Tracing e Correlação de Logs"
                ],
                "atividades": [
                    "Fixação da proporção de testes unitários, testes de contrato e E2E (50 min)",
                    "Revisão escrita sobre Testes de Contrato (40 min)",
                    "Estudo dos pilares de observabilidade e resolução das questões 4 e 5 do simulado (60 min)"
                ]
            },
            {
                "dia": 5,
                "horas_previstas": 2.5,
                "foco_principal": "Simulação Geral da Avaliação e Revisão Ativa de Erros",
                "topicos_alvo": [
                    "Todos os tópicos de Alta Complexidade revisados em ciclo rápido"
                ],
                "atividades": [
                    "Refazer o simulado completo de 5 questões objetivas cronometrado (30 min)",
                    "Análise detalhada do gabarito comentado focado nas justificativas dos distratores (45 min)",
                    "Revisão final dos tópicos classificados como Alta Complexidade (Sagas e Circuit Breaker) (45 min)",
                    "Descanso mental pré-prova e alinhamento de estratégias de resolução (30 min)"
                ]
            }
        ]
    }
}
