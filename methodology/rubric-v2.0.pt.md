# Rubrica de Comparação de Métodos v2.0 (congelada)

| Campo | Valor |
|---|---|
| Versão | 2.0, congelada em 2026-11-26, antes de qualquer medição das lentes novas |
| Base | Rubrica de maturidade v1.0 (16 critérios), SHA-256 `a6e3953725b67db0189e188c1495ee9b54975e48f65c28baaa01f459b69cf9a4`, anexada em `anexos/metodologia-v1.0.md` |
| Regra de congelamento | Qualquer alteração depois da primeira medição exige nova versão e nova medição de todos os métodos |

## 0. O que muda da v1 para a v2

A v2 **não altera** os 16 critérios, as âncoras nem os pesos da v1. O total de maturidade continua sendo o número principal. A v2 acrescenta quatro lentes **descritivas e sem peso**, que respondem perguntas que a v1 não respondia:

| Lente | Pergunta | Tipo |
|---|---|---|
| L1 Maturidade (v1) | Quão maduro é o caminho padrão do método para um time profissional? | Score ponderado 0–100 (principal) |
| L2 Teto de capacidade | Quão maduro é o melhor caminho que o método oferece, mesmo opt-in? | Score ponderado 0–100, mostrado **ao lado** do L1 |
| L3 Nível de autonomia | Quanto do trabalho roda sem um humano? | Escala A0–A5, descritiva |
| L4 Matriz de funcionalidades | Quais funcionalidades o método entrega? | 34 itens ●/◐/○, cobertura em % |
| L5 Footprint de tokens | Quanto contexto o método consome por construção? | Tokens medidos estaticamente (proxy) |

Nenhuma lente nova entra no total ponderado: autonomia e tokens já têm critérios na v1 (C8, C13), e somá-los de novo contaria a mesma coisa duas vezes.

## 1. L2: teto de capacidade

**Regra.** O L1 limita a nota 2 a mecanismos opt-in ou fora do caminho que o método escolhe para o cenário de referência R (§2.2 da v1). O L2 remove só esse limite: cada critério recebe o maior nível sustentado por **qualquer caminho distribuído** pelo método, com as mesmas âncoras e as mesmas regras de evidência da v1.

**Seleção mecânica das células.** São reexaminadas só as células cujo scorecard da v1 cita, na justificativa ou no primeiro requisito não atendido, o limite opt-in, o caminho padrão, a rota escolhida ou um mecanismo "opcional". As demais células ficam iguais às do L1.

**Leitura.** L2 − L1 mede quanto valor o método deixa fora do caminho padrão. A diferença tende a favorecer métodos com muitas skills opcionais; por isso o L2 nunca substitui o L1.

## 2. L3: nível de autonomia (cumulativo, exige evidência)

Cada nível exige os requisitos dele e de todos os anteriores, com citação de arquivo. Evidência só de documentação limita a A2 (método aberto) ou A3 (produto fechado).

| Nível | Nome | Requisito |
|---|---|---|
| A0 | Biblioteca de prompts | Instruções isoladas; o humano invoca cada passo |
| A1 | Workflow guiado | Workflows de vários passos definidos; o agente para e espera o humano entre passos |
| A2 | Tarefa completa | O agente executa uma tarefa inteira (planejar → codar → testar) numa sessão, com condições de parada definidas |
| A3 | Orquestração na sessão | O agente despacha subagentes com contexto novo e encadeia várias tarefas sem humano por tarefa, dentro de uma sessão |
| A4 | Execução desacompanhada multi-sessão | Um loop externo abre sessões novas por tarefa, com estado persistido e retomada, sem humano entre tarefas |
| A5 | Fluxo contínuo | A4 + execução paralela ou integração das tarefas sem humano, do backlog à mudança integrada |

**Leitura obrigatória.** Autonomia não é qualidade. A L3 é sempre apresentada cruzada com C8 (segurança da execução autônoma) e com o total L1, em gráfico de duas dimensões. Um método A4 com C8 baixo é **mais arriscado**, não melhor.

## 3. L4: matriz de funcionalidades

A lista foi derivada de uma taxonomia genérica do ciclo de desenvolvimento (descoberta → design → construção → verificação → autonomia → governança → operação → ecossistema) e **não** das funcionalidades de nenhum método avaliado.

**Valores.** ● = presente no caminho padrão para R (2 pontos) · ◐ = opt-in, parcial ou só documentado (1 ponto) · ○ = ausente (0). Cada ● ou ◐ exige citação. **Cobertura** = pontos ÷ 68.

| ID | Grupo | Funcionalidade |
|---|---|---|
| F1 | Descoberta | Elicitação estruturada (entrevista, perguntas obrigatórias) |
| F2 | Descoberta | Template de spec com critérios de aceite testáveis |
| F3 | Descoberta | Crítica independente da spec |
| F4 | Descoberta | Controle de mudança da spec (versionamento, impacto) |
| F5 | Design | Decomposição em tarefas com dependências explícitas |
| F6 | Design | Registro de decisões (ADR ou equivalente) |
| F7 | Design | Mapeamento do código existente / contexto de projeto (brownfield) |
| F8 | Design | Roteamento por tamanho ou risco (caminhos leve e pesado) |
| F9 | Construção | Test-first (teste falhando antes do código) |
| F10 | Construção | Debugging sistemático (procedimento de causa raiz) |
| F11 | Construção | Agentes ou personas especializados por papel |
| F12 | Construção | Subagentes com contexto isolado e brief explícito |
| F13 | Verificação | Gate de verificação com evidência fresca de comandos |
| F14 | Verificação | Review por contexto independente do autor |
| F15 | Verificação | Múltiplas lentes de review com consolidação |
| F16 | Verificação | Revisão de segurança ou threat modeling |
| F17 | Autonomia | Loop de iteração com limite numérico e ação no limite |
| F18 | Autonomia | Execução multi-sessão sem humano entre tarefas |
| F19 | Autonomia | Isolamento da execução (branch, worktree ou sandbox) |
| F20 | Autonomia | Estado persistido e retomada após interrupção |
| F21 | Autonomia | Limites impostos pelo ambiente (hooks, permissões, sandbox) |
| F22 | Governança | Aprovações humanas registradas (quem, quando, versão) |
| F23 | Governança | IDs rastreáveis requisito → tarefa → teste |
| F24 | Governança | Trilha de auditoria exportável ou checada por ferramenta |
| F25 | Operação | Release com rollback |
| F26 | Operação | Incidente e postmortem |
| F27 | Operação | Retrospectiva que altera o ambiente (instruções, checks) |
| F28 | Operação | Memória ou base de conhecimento entre sessões |
| F29 | Ecossistema | Suporte oficial a 3 ou mais plataformas de agente |
| F30 | Ecossistema | Instalador e atualização versionados |
| F31 | Ecossistema | Validação automática do próprio método (CI, lint, schema) |
| F32 | Economia | Telemetria de tokens ou custo |
| F33 | Economia | Orçamento de tamanho de contexto ou artefato |
| F34 | Economia | Evals que medem o comportamento do método |

## 4. L5: footprint de tokens (medição estática)

**Host de referência.** A plataforma primária declarada pelo método (para multiplataforma, a primeira listada no README).

| Medida | O que entra |
|---|---|
| T1 Sempre carregado | Arquivos de instrução que o host injeta em toda sessão (CLAUDE.md, AGENTS.md, copilot-instructions, regras always-on) + descrições (frontmatter) de todas as skills/agentes/comandos que o host pré-carrega |
| T2 Entrada | Corpo da skill, comando ou agente de entrada + arquivos que ele manda ler na ativação |
| T3 Caminho R | Arquivos que o caminho padrão para R manda ler, do início ao fim de uma feature média (soma, sem repetição) |
| T0 Corpus | Todo o texto Markdown/YAML/TOML do método (referência de tamanho) |

**Procedimento.** Um avaliador lista os arquivos de T1, T2 e T3 com citação de onde a leitura é exigida. Um único script conta os tokens de todos os métodos com o mesmo tokenizador (`tiktoken o200k_base`, ou caracteres ÷ 4 se indisponível), localmente. O resultado é um **proxy**: tokenizadores de outros modelos diferem em cerca de ±20%.

**Fora do escopo.** O consumo em execução (tokens gastos para entregar uma feature) não é medido nesta versão. A §6 define o protocolo de piloto para medi-lo.

## 5. Regras de justiça (aplicam-se a todas as lentes)

1. Mesmo procedimento e mesmo contrato de saída para todos os métodos.
2. Evidência por arquivo; marketing, roadmap e "em breve" não contam.
3. Na dúvida, o nível menor e a confiança menor.
4. Produto fechado: teto por evidência documental, marcado na tabela.
5. Diferença de calibração entre rodadas de avaliadores é mostrada como sensibilidade, nunca como ajuste.
6. Um avaliador por método nas lentes descritivas, com auditoria de 15% das células sorteada com seed fixa.

## 6. Protocolo futuro: consumo de tokens em execução

Mesma tarefa de referência (feature R em repositório público fixo), mesmo modelo e mesmo host para todos os métodos, 3 execuções cada. Medir tokens de entrada, saída e cache por execução a partir da telemetria do host; reportar mediana e amplitude; descartar execução que não atinja os critérios de aceite. Resultado só é publicado com as 3 execuções completas.
