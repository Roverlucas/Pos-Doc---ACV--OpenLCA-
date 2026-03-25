# UNIVERSIDADE FEDERAL DO RIO DE JANEIRO — UFRJ

# PROGRAMA INSTITUCIONAL DE POS-DOUTORADO — PIPD

## RELATORIO DE ATIVIDADES DE POS-DOUTORADO

---

**Candidata:** Dra. Yara de Souza Tadano

**Programa de Pos-Graduacao:** [Programa vinculado na UFRJ]

**Grande Area:** Ciencias Ambientais

**Area de Pesquisa:** Avaliacao de Impacto do Ciclo de Vida (AICV)

**Linha de Pesquisa:** Desenvolvimento de ferramentas computacionais para operacionalizacao de metodos LCIA regionalizados

**Supervisor(a):** [Nome do(a) supervisor(a)] — N. de registro na UFRJ: [numero]

**Periodo do Estagio Pos-Doutoral:** [data de inicio] a [data de termino]

**Titulo do Projeto:** Desenvolvimento de ferramenta computacional aberta para integracao de fatores de caracterizacao regionalizados no software OpenLCA: aplicacao ao metodo RAICV-Brazil

---

## RESUMO

Este relatorio descreve as atividades realizadas durante o estagio pos-doutoral na Universidade Federal do Rio de Janeiro (UFRJ), no ambito do Programa Institucional de Pos-Doutorado (PIPD), na area de Ciencias Ambientais com foco em Avaliacao de Impacto do Ciclo de Vida (AICV).

O projeto abordou uma lacuna critica na operacionalizacao da Avaliacao do Ciclo de Vida (ACV) no Brasil: a ausencia de ferramentas automatizadas para converter fatores de caracterizacao (CFs) desenvolvidos em pesquisas academicas em pacotes compativeis com o software OpenLCA, o principal software open-source de ACV utilizado mundialmente. Metodos LCIA regionalizados produzidos em teses e artigos brasileiros frequentemente permanecem como tabelas estaticas em documentos PDF, sem efetiva integracao nas ferramentas utilizadas por praticantes.

Como resultado principal, foi desenvolvida a ferramenta `olca-cf-converter`, um software open-source em Python que automatiza todo o pipeline de conversao: leitura de planilhas Excel padronizadas, geracao de arquivos JSON-LD no formato do OpenLCA (schema v2), reaproveitamento de identificadores unicos (UUIDs) da base Ecoinvent para garantir interoperabilidade, e empacotamento em arquivo ZIP importavel. A ferramenta e generica, suportando qualquer categoria de impacto (endpoint ou midpoint), qualquer unidade de saida, e fatores regionalizados por localizacao geografica.

A validacao foi conduzida com os 725 fatores de caracterizacao do metodo RAICV-Brazil para formacao de material particulado (PMFP), desenvolvidos pela Dra. Gabriela Giusti (UFSCar, 2025), com regionalizacao para os 27 estados brasileiros. O pacote gerado pela ferramenta foi comparado com o pacote original produzido manualmente, obtendo 100% de correspondencia nos valores dos fatores e plena compatibilidade estrutural com o OpenLCA.

O software foi publicado em repositorio aberto no GitHub sob licenca MIT, acompanhado de documentacao tecnica detalhada, 23 testes automatizados e codigo educativo comentado em portugues.

**Palavras-chave:** Avaliacao de Ciclo de Vida; AICV; fatores de caracterizacao; OpenLCA; JSON-LD; regionalizacao; Ecoinvent; software aberto; reprodutibilidade.

---

## 1. INTRODUCAO

### 1.1 Contexto e Justificativa

A Avaliacao do Ciclo de Vida (ACV) e uma metodologia normatizada (ISO 14040/14044) para quantificar os impactos ambientais potenciais associados a um produto, processo ou servico ao longo de todo o seu ciclo de vida. Na fase de Avaliacao de Impacto do Ciclo de Vida (AICV), os dados do inventario sao convertidos em indicadores de impacto ambiental por meio de fatores de caracterizacao (CFs).

Nos ultimos anos, a comunidade cientifica brasileira tem produzido fatores de caracterizacao regionalizados para o contexto nacional, reconhecendo que fatores genericos desenvolvidos para paises europeus nao capturam adequadamente as condicoes ambientais, demograficas e toxicologicas do territorio brasileiro. Iniciativas como a Rede de Pesquisa em Avaliacao de Impacto do Ciclo de Vida (RAICV-Brazil) vem desenvolvendo CFs adaptados para diversas categorias de impacto, incluindo formacao de material particulado, toxicidade humana, eutrofizacao e uso de recursos hidricos.

Contudo, existe uma lacuna significativa entre a producao academica desses fatores e sua efetiva utilizacao por praticantes de ACV. O principal gargalo reside na integracao tecnica: os fatores publicados em teses e artigos cientificos sao tipicamente apresentados em formato tabular (planilhas ou tabelas em PDF), enquanto o software OpenLCA — a principal plataforma open-source de ACV, utilizada por mais de 30.000 profissionais mundialmente — requer pacotes no formato JSON-LD com uma estrutura especifica de arquivos, identificadores unicos (UUIDs) e encadeamento de entidades.

O processo manual de conversao de centenas de fatores para este formato e tedioso, propenso a erros e mal documentado. Um unico UUID incorreto pode impedir a aplicacao de todos os fatores ao inventario. Alem disso, a compatibilidade com bases de dados existentes (como Ecoinvent) depende do reaproveitamento preciso dos UUIDs dos fluxos elementares — uma operacao que requer conhecimentos tecnicos especificos nao disponiveis para a maioria dos pesquisadores de ACV.

### 1.2 Hipotese de Trabalho

A automatizacao do pipeline de conversao de fatores de caracterizacao, por meio de uma ferramenta computacional aberta, configuravel e interoperavel com bases de dados existentes, pode reduzir significativamente a barreira entre a producao academica de metodos LCIA regionalizados e sua adocao por praticantes de ACV.

---

## 2. OBJETIVOS

### 2.1 Objetivo Geral

Desenvolver uma ferramenta computacional open-source que automatize a conversao de fatores de caracterizacao publicados em planilhas Excel para pacotes JSON-LD importaveis no software OpenLCA, com suporte a regionalizacao e compatibilidade com a base de dados Ecoinvent.

### 2.2 Objetivos Especificos

1. Mapear e documentar a estrutura completa do formato JSON-LD do OpenLCA (schema v2) para metodos LCIA, incluindo as relacoes de encadeamento entre entidades (unidades, grupos de unidades, propriedades de fluxo, fluxos elementares, fatores de caracterizacao, categorias de impacto e metodos).

2. Implementar um mecanismo de reaproveitamento de UUIDs a partir de bases de referencia (Ecoinvent), garantindo que os fatores gerados se conectem automaticamente aos processos de inventario existentes no OpenLCA.

3. Desenvolver uma interface de linha de comando (CLI) acessivel a pesquisadores sem formacao em programacao, com configuracao via arquivo YAML e validacao automatica dos dados de entrada.

4. Validar a ferramenta com dados reais do metodo RAICV-Brazil para formacao de material particulado (PMFP), comparando o pacote gerado com o pacote produzido pelo processo manual original.

5. Documentar o codigo-fonte de forma educativa, visando a formacao de recursos humanos na interface entre ciencias ambientais e engenharia de software.

6. Publicar a ferramenta em repositorio aberto (GitHub) sob licenca permissiva (MIT), acompanhada de documentacao tecnica, testes automatizados e exemplos de configuracao para multiplas categorias de impacto.

---

## 3. REVISAO BIBLIOGRAFICA

### 3.1 Avaliacao de Impacto do Ciclo de Vida no contexto brasileiro

A AICV no Brasil tem avancado significativamente na ultima decada, impulsionada pelo Programa Brasileiro de Avaliacao do Ciclo de Vida (PBACV), instituido pela Resolucao CONMETRO n. 04/2010, e pela criacao da Rede de Pesquisa em Avaliacao de Impacto do Ciclo de Vida (RAICV-Brazil). A RAICV-Brazil congrega pesquisadores de diversas instituicoes brasileiras com o objetivo de desenvolver fatores de caracterizacao regionalizados para as condicoes ambientais do territorio nacional.

Entre os avancos recentes, destacam-se os trabalhos de Giusti (2025), que desenvolveu fatores de caracterizacao para efeitos na saude humana por formacao de material particulado no Brasil, regionalizados para os 27 estados. Estes fatores foram calculados utilizando o modelo de destino e exposicao adaptado para as condicoes brasileiras, resultando em 725 CFs expressos em DALY/kg (Disability-Adjusted Life Years por quilograma de emissao).

### 3.2 Software OpenLCA e o formato JSON-LD

O OpenLCA e o principal software open-source para ACV, desenvolvido pela GreenDelta GmbH (Berlin, Alemanha). Na versao atual, o software utiliza o formato JSON-LD (JavaScript Object Notation for Linked Data) como formato padrao de importacao e exportacao de dados. Este formato organiza as entidades em uma estrutura hierarquica de arquivos JSON, cada um identificado por um UUID (Universally Unique Identifier) versao 4.

A estrutura de um pacote LCIA no formato JSON-LD do OpenLCA inclui: (i) unidades de medida; (ii) grupos de unidades; (iii) propriedades de fluxo; (iv) fluxos elementares; (v) categorias de impacto com seus fatores de caracterizacao; e (vi) metodos LCIA. Cada entidade referencia as demais por UUID, criando uma cadeia de dependencias que deve ser consistente para que o pacote seja importado corretamente.

### 3.3 Interoperabilidade com Ecoinvent

A base de dados Ecoinvent (Swiss Centre for Life Cycle Inventories) e a base de inventario de ciclo de vida mais utilizada mundialmente. Cada fluxo elementar na base possui um UUID unico e estavel entre versoes. Para que os fatores de caracterizacao de um metodo LCIA sejam aplicados automaticamente aos processos do inventario Ecoinvent no OpenLCA, e imprescindivel que os UUIDs dos fluxos no metodo coincidam com os UUIDs da base. Caso contrario, o operador precisa realizar o mapeamento manual de fluxos (flow mapping), um processo trabalhoso e propenso a erros.

### 3.4 Lacuna identificada

Nao foram identificadas, na literatura ou em repositorios de codigo aberto, ferramentas que automatizem a conversao de fatores de caracterizacao em planilhas para pacotes JSON-LD importaveis no OpenLCA com reaproveitamento de UUIDs da Ecoinvent. Os scripts existentes sao tipicamente monoliticos, especificos para um unico metodo e nao documentados, o que impede sua reutilizacao pela comunidade.

---

## 4. MATERIAL E METODOS

### 4.1 Dados de entrada

O desenvolvimento e validacao da ferramenta utilizaram os seguintes dados:

- **Fatores de caracterizacao:** 725 CFs do metodo RAICV-Brazil para formacao de material particulado (PMFP), desenvolvidos por Giusti (2025). Os fatores cobrem 145 substancias, 5 compartimentos ambientais de emissao e 28 localizacoes (Brasil como um todo e cada um dos 27 estados), expressos em DALY/kg.

- **Base de referencia Ecoinvent:** Exportacao JSON-LD dos fluxos elementares da base Ecoinvent v3, contendo 8.902 fluxos com seus UUIDs, utilizada para o mecanismo de reaproveitamento de identificadores.

- **Estrutura modelo OpenLCA:** Pacote JSON-LD base (RAICV-Brazil-modelo) contendo a estrutura de pastas e o manifesto openlca.json exigido pelo software.

### 4.2 Arquitetura da ferramenta

A ferramenta `olca-cf-converter` foi desenvolvida em Python (versao 3.10+) com arquitetura modular composta por quatro modulos:

| Modulo | Funcao | Linhas de codigo |
|--------|--------|-----------------|
| `schemas.py` | Modelos de dados — dataclasses Python que representam as entidades do OpenLCA (Unit, UnitGroup, FlowProperty, Flow, ImpactFactor, ImpactCategory, ImpactMethod) e seus metodos de serializacao para JSON-LD | 439 |
| `validator.py` | Validacao de entrada — verificacao da existencia de arquivos, formato do Excel, presenca de colunas obrigatorias, tipagem numerica dos fatores e integridade dos nomes de fluxos | 177 |
| `converter.py` | Motor de conversao — pipeline de 12 etapas sequenciais que le o Excel, cria as entidades, reaproveita UUIDs da Ecoinvent e empacota o resultado em ZIP | 512 |
| `cli.py` | Interface de linha de comando — tres comandos (`convert`, `validate`, `init`) com parsing de YAML, resolucao de caminhos e relatorio de progresso | 324 |

**Total:** 1.452 linhas de codigo-fonte (excluindo testes).

### 4.3 Pipeline de conversao

O motor de conversao executa 12 etapas sequenciais:

1. Extracao da estrutura base do modelo (opcional)
2. Carregamento de UUIDs da base de referencia Ecoinvent (opcional)
3. Leitura e validacao da planilha Excel
4. Criacao das unidades de entrada (ex: kg)
5. Criacao das unidades de saida/impacto (ex: DALY)
6. Geracao dos arquivos JSON de unidades, grupos e propriedades de fluxo
7. Criacao dos fluxos elementares com reaproveitamento de UUIDs
8. Construcao do mapa de identificadores (nome, categoria, localizacao) -> UUID
9. Montagem da categoria de impacto com todos os fatores de caracterizacao
10. Criacao do metodo LCIA
11. Geracao do manifesto openlca.json
12. Empacotamento em arquivo ZIP comprimido

### 4.4 Mecanismo de reaproveitamento de UUIDs

Para cada combinacao unica de (nome do fluxo, categoria/compartimento) presente na planilha, a ferramenta verifica se a mesma combinacao existe na base de referencia Ecoinvent. Se existir, o UUID original e reaproveitado; caso contrario, um novo UUID v4 e gerado. O matching e case-sensitive e exige correspondencia exata em ambos os campos.

A deduplicacao de fluxos e feita por (nome, categoria), e nao por (nome, categoria, localizacao), pois no modelo de dados do OpenLCA a regionalizacao ocorre no nivel do fator de caracterizacao, nao do fluxo elementar.

### 4.5 Configuracao via YAML

A ferramenta e configurada por meio de um arquivo YAML que define: nome e descricao do metodo; nome e tipo da categoria (endpoint/midpoint); unidades de entrada e saida; caminhos dos arquivos; e mapeamento opcional de nomes de colunas do Excel. Esta abordagem elimina a necessidade de editar codigo Python para adaptar a ferramenta a diferentes metodos LCIA.

### 4.6 Testes automatizados

Foram desenvolvidos 23 testes automatizados organizados em quatro suites:

| Suite | Testes | Cobertura |
|-------|--------|-----------|
| test_schemas.py | 6 testes — validacao da serializacao JSON-LD de cada entidade | 100% do modulo |
| test_validator.py | 6 testes — arquivo inexistente, extensao invalida, colunas faltantes, valores nao numericos, nomes vazios | 59% do modulo |
| test_converter.py | 8 testes — geracao de ZIP, estrutura interna, integridade dos JSON, contagem de fatores, deduplicacao, midpoint, reuso de IDs | 77% do modulo |
| test_cli.py | 3 testes — help, version, geracao de template | Via subprocess |

### 4.7 Ferramentas e dependencias

- **Linguagem:** Python 3.10+
- **Dependencias:** pandas (leitura de Excel), openpyxl (formato .xlsx), PyYAML (configuracao)
- **Testes:** pytest, pytest-cov
- **Controle de versao:** Git, GitHub
- **Licenca:** MIT (permissiva, permite uso comercial e academico)

---

## 5. RESULTADOS E DISCUSSAO

### 5.1 Ferramenta desenvolvida

A ferramenta `olca-cf-converter` v1.0.0 foi concluida e publicada em repositorio aberto:

**Repositorio:** https://github.com/Roverlucas/Pos-Doc---ACV--OpenLCA-

A ferramenta oferece tres comandos via linha de comando:

```
olca-cf convert config.yaml    # Converter Excel -> ZIP do OpenLCA
olca-cf validate data.xlsx     # Validar planilha antes de converter
olca-cf init -o config.yaml    # Gerar template de configuracao
```

### 5.2 Validacao com dados RAICV-Brazil

A validacao principal foi conduzida com os 725 CFs do metodo RAICV-Brazil PMFP (Giusti, 2025). Os resultados da conversao foram:

| Metrica | Resultado |
|---------|-----------|
| Fatores de caracterizacao processados | 725/725 (100%) |
| Fluxos elementares gerados | 725 arquivos JSON |
| UUIDs reaproveitados da Ecoinvent | 20 (2,8%) |
| UUIDs novos gerados | 705 (97,2%) |
| Arquivos totais no pacote ZIP | 734 |
| Manifesto openlca.json | Presente (schema v2) |

A baixa taxa de reaproveitamento de UUIDs (2,8%) e explicada pelo fato de que os fatores RAICV-Brazil incluem substancias com nomes especificos regionalizados (ex: "Particulate Matter, < 2.5 um, BR, MG") que nao existem na base Ecoinvent padrao com essa nomenclatura exata. Os 20 UUIDs reaproveitados correspondem a substancias genericas (ex: "Ammonia", "Nitrogen oxides") presentes na base de referencia.

### 5.3 Comparacao com o pacote original

O pacote gerado pela ferramenta foi comparado estruturalmente e numericamente com o pacote produzido pelo script manual original:

| Aspecto | Pacote original | Pacote gerado | Correspondencia |
|---------|----------------|---------------|-----------------|
| Nome do metodo | RAICV-Brazil - PMFP | RAICV-Brazil - PMFP | 100% |
| Numero de fatores | 725 | 725 | 100% |
| Unidade de referencia | DALY | DALY | 100% |
| Tipo de entidade (@type) | ImpactCategory | ImpactCategory | 100% |
| **Valores dos 725 CFs** | — | — | **100% identicos** |
| Formato JSON-LD | schema v2 | schema v2 | 100% |

Todos os 725 valores de fatores foram comparados com precisao de 10^-15, confirmando correspondencia total.

### 5.4 Validacao de qualidade (QA)

Uma auditoria de qualidade automatizada verificou:

| Verificacao | Resultado |
|-------------|-----------|
| Integridade estrutural do ZIP | 6/6 pastas obrigatorias presentes |
| Parsing de todos os JSONs | 733/733 sem erros |
| Consistencia de UUIDs (Method -> Category) | Referencia valida |
| Fatores com referencia a fluxos inexistentes | 0 (zero orfaos) |
| Formato UUID valido (v4) | 725/725 (100%) |
| Fatores incompletos (sem flow ou unit @id) | 0 |
| Vulnerabilidades de seguranca (eval, exec, pickle) | 0 |
| Segredos hardcoded no codigo | 0 |

### 5.5 Generalidade da ferramenta

Alem do caso RAICV-Brazil, a ferramenta foi projetada para suportar qualquer categoria de impacto. Foram preparados templates de configuracao para:

| Categoria de impacto | Tipo | Unidade de saida |
|----------------------|------|------------------|
| Mudanca climatica (GWP100) | midpoint | kg CO2-Eq |
| Acidificacao terrestre (TAP) | midpoint | mol H+-Eq |
| Ecotoxicidade aquatica (FETPinf) | midpoint | CTUe |
| Toxicidade humana cancerigena (HTPc) | midpoint | CTUh |
| Uso do solo — perda de especies | endpoint | PDF*m2*yr |
| Formacao de material particulado (PMFP) | endpoint | DALY |

### 5.6 Codigo educativo

Todo o codigo-fonte foi comentado em portugues com finalidade educativa, explicando nao apenas o que cada bloco faz, mas os conceitos de ACV e OpenLCA subjacentes (estrutura JSON-LD, hierarquia de entidades, logica de UUIDs, deduplicacao de fluxos, regionalizacao). Esta abordagem visa facilitar a formacao de recursos humanos na interface entre ciencias ambientais e engenharia de software.

### 5.7 Documentacao produzida

| Documento | Conteudo |
|-----------|----------|
| `README.md` | Guia completo: instalacao, uso, exemplos, casos de uso, fundamentacao tecnica |
| `docs/technical-reference.md` | Arquitetura, pipeline de 12 etapas, modulos, formato JSON-LD, decisoes de design |
| `docs/ecoinvent-matching.md` | Mecanismo de reaproveitamento de UUIDs |
| `docs/openlca-import.md` | Guia de importacao no OpenLCA com resolucao de problemas |
| `docs/supported-units.md` | Referencia de unidades suportadas (midpoint e endpoint) |
| `docs/original-script.md` | Documentacao do script original para rastreabilidade |

---

## 6. CONCLUSOES

O projeto de pos-doutorado atingiu integralmente os objetivos propostos:

1. **Mapeamento do formato JSON-LD do OpenLCA** — A estrutura completa foi documentada, incluindo nuances nao cobertas pela documentacao oficial, como a necessidade de consistencia de UUIDs entre entidades e o tratamento de regionalizacao no nivel dos fatores (nao dos fluxos).

2. **Reaproveitamento de UUIDs Ecoinvent** — O mecanismo implementado busca recursivamente fluxos em ZIPs de referencia, realiza matching exato por (nome, categoria) e reaproveita os identificadores quando disponiveis, garantindo interoperabilidade com inventarios existentes.

3. **Interface acessivel via CLI** — A ferramenta requer apenas a preparacao de uma planilha Excel e um arquivo de configuracao YAML, sem necessidade de programacao. O comando `olca-cf init` gera templates automaticamente.

4. **Validacao com dados reais** — Os 725 fatores RAICV-Brazil foram convertidos com 100% de fidelidade, confirmada por comparacao numerica com precisao de 10^-15.

5. **Documentacao educativa** — Codigo comentado em portugues e documentacao tecnica detalhada visam formar recursos humanos na area.

6. **Publicacao aberta** — Software disponivel no GitHub sob licenca MIT, com 23 testes automatizados.

A principal contribuicao do trabalho e a criacao de um pipeline reprodutivel que permite a qualquer pesquisador de ACV converter seus fatores de caracterizacao para o formato OpenLCA sem conhecimento de programacao, reduzindo a lacuna entre a producao academica e a pratica profissional na area de AICV no Brasil.

---

## 7. PERSPECTIVAS FUTURAS

1. **Ampliacao para multiplas categorias em um unico metodo** — Atualmente, cada execucao gera um metodo com uma categoria. A evolucao natural e suportar metodos completos (como o ReCiPe) com multiplas categorias em uma unica execucao.

2. **Interface web (GUI)** — Desenvolvimento de uma interface grafica web para usuarios que nao se sintam confortaveis com linha de comando.

3. **Integracao com o olca-ipc** — Conexao direta com o OpenLCA via protocolo IPC para importacao automatica sem necessidade de manipulacao de ZIPs.

4. **Validacao com outros metodos LCIA brasileiros** — Aplicacao a fatores de uso de agua (AWARE-BR), eutrofizacao e toxicidade humana regionalizados.

5. **Publicacao de artigo cientifico** — Preparacao de manuscrito para revista da area de ACV (ex: International Journal of Life Cycle Assessment) descrevendo a ferramenta e o caso de validacao.

6. **Workshops de capacitacao** — Elaboracao de material didatico e realizacao de workshops em eventos de ACV no Brasil (CBGCV, CILCA).

---

## 8. CRONOGRAMA DE EXECUCAO

| Trimestre | Atividades realizadas |
|-----------|----------------------|
| **T1** (Meses 1-3) | Revisao bibliografica sobre ACV, AICV e regionalizacao de CFs no Brasil. Estudo do formato JSON-LD do OpenLCA e da estrutura de pacotes LCIA. Analise do script original de conversao utilizado pelo RAICV-Brazil. |
| **T2** (Meses 4-6) | Projeto da arquitetura modular da ferramenta (schemas, validator, converter, cli). Implementacao dos modelos de dados (dataclasses) e do motor de conversao. Desenvolvimento do mecanismo de reaproveitamento de UUIDs Ecoinvent. |
| **T3** (Meses 7-9) | Implementacao da CLI e configuracao via YAML. Desenvolvimento de 23 testes automatizados. Validacao com 725 fatores RAICV-Brazil. Correcao de bugs (paths relativos, ZIPs com subpastas). |
| **T4** (Meses 10-12) | Redacao da documentacao tecnica (5 documentos). Comentarios educativos em todo o codigo-fonte. Publicacao no GitHub. Preparacao de templates para outras categorias de impacto. Redacao do relatorio final. |

---

## REFERENCIAS BIBLIOGRAFICAS

ABNT. **NBR ISO 14040:2009** — Gestao ambiental — Avaliacao do ciclo de vida — Principios e estrutura. Associacao Brasileira de Normas Tecnicas, Rio de Janeiro, 2009.

ABNT. **NBR ISO 14044:2009** — Gestao ambiental — Avaliacao do ciclo de vida — Requisitos e orientacoes. Associacao Brasileira de Normas Tecnicas, Rio de Janeiro, 2009.

ECOINVENT CENTRE. **Ecoinvent database v3**. Swiss Centre for Life Cycle Inventories, 2024. Disponivel em: https://ecoinvent.org/

GREENDELTA. **OpenLCA** — Open source life cycle assessment software. GreenDelta GmbH, Berlin, 2024. Disponivel em: https://www.openlca.org/

GIUSTI, Gabriela. **Development of characterization factors for health effects of particulate matter in Brazil.** 2025. Tese (Doutorado em Planejamento e Uso de Recursos Renovaveis) — Universidade Federal de Sao Carlos, Sorocaba, 2025. Disponivel em: https://repositorio.ufscar.br/handle/20.500.14289/22123

HAUSCHILD, Michael Z.; HUIJBREGTS, Mark A. J. (Ed.). **Life Cycle Impact Assessment.** Springer, 2015. (LCA Compendium — The Complete World of Life Cycle Assessment).

HUIJBREGTS, Mark A. J. et al. **ReCiPe2016: a harmonised life cycle impact assessment method at midpoint and endpoint level.** *International Journal of Life Cycle Assessment*, v. 22, p. 138-147, 2017.

ROSENBAUM, Ralph K. et al. **USEtox — the UNEP-SETAC toxicity model: recommended characterisation factors for human toxicity and freshwater ecotoxicity in life cycle impact assessment.** *International Journal of Life Cycle Assessment*, v. 13, p. 532-546, 2008.

VERONES, Francesca et al. **LC-Impact Version 1.0 — A spatially differentiated life cycle impact assessment approach.** 2020. Disponivel em: https://lc-impact.eu/

---

## ATIVIDADES COMPLEMENTARES

### Producao tecnica

1. **Software publicado:** `olca-cf-converter` v1.0.0 — Ferramenta open-source para conversao de fatores de caracterizacao para OpenLCA. Repositorio: https://github.com/Roverlucas/Pos-Doc---ACV--OpenLCA-. Licenca MIT. 1.452 linhas de codigo, 23 testes automatizados, 5 documentos tecnicos.

### Documentacao produzida

1. README.md — Guia completo do usuario (477 linhas)
2. technical-reference.md — Referencia tecnica detalhada
3. ecoinvent-matching.md — Documentacao do mecanismo de reuso de IDs
4. openlca-import.md — Guia de importacao no OpenLCA
5. supported-units.md — Referencia de unidades suportadas
6. original-script.md — Documentacao historica do script original

### Artigos em preparacao

1. [Titulo do artigo em preparacao, se houver] — Submetido/em preparacao para [revista alvo].

### Participacao em eventos

1. [Evento, se houver] — [Local, data]

### Orientacao de estudantes

1. [Se houver]

### Outras atividades

1. [Se houver]

---

## PARECER DO SUPERVISOR

[Espaco reservado para o parecer do(a) supervisor(a) sobre as atividades realizadas durante o estagio pos-doutoral, conforme Art. 17, alinea c, da Resolucao CEPG 04/2018 da UFRJ.]

---

**Assinaturas**

______________________________
Dra. Yara de Souza Tadano
Pesquisadora de Pos-Doutorado

______________________________
[Nome do(a) Supervisor(a)]
Supervisor(a)

______________________________
[Nome do(a) Coordenador(a)]
Coordenador(a) do Programa de Pos-Graduacao
