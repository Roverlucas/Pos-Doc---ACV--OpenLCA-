# ANEXO 2 — DOCUMENTACAO TECNICA DO CODIGO-FONTE

## olca-cf-converter v1.0.0 — Referencia Tecnica Completa

---

## 1. VISAO GERAL DA ARQUITETURA

### 1.1 Diagrama de componentes

```
                         +------------------+
                         |   config.yaml    |  Arquivo de configuracao do usuario
                         +--------+---------+
                                  |
                                  v
                         +--------+---------+
                         |     cli.py       |  Ponto de entrada — parsing de
                         |   (324 linhas)   |  argumentos e orquestracao
                         +--------+---------+
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
           +--------+---------+       +--------+---------+
           |  validator.py    |       |  converter.py    |
           |  (177 linhas)    |       |  (512 linhas)    |
           |                  |       |                  |
           | Validacao de     |       | Pipeline de 12   |
           | entrada (Excel   |       | etapas: leitura, |
           | + config paths)  |       | criacao de       |
           +---------+--------+       | entidades,       |
                     |                | reuso de UUIDs,  |
                     v                | empacotamento    |
           +---------+--------+       +--------+---------+
           | pandas DataFrame |                |
           | (dados brutos)   |                v
           +------------------+       +--------+---------+
                                      |   schemas.py     |
                                      |  (439 linhas)    |
                                      |                  |
                                      | Dataclasses que  |
                                      | representam as   |
                                      | entidades OpenLCA|
                                      | e serializam     |
                                      | para JSON-LD     |
                                      +--------+---------+
                                               |
                                               v
                                      +--------+---------+
                                      |   output.zip     |
                                      | Pacote importavel|
                                      | pelo OpenLCA     |
                                      +------------------+
```

### 1.2 Fluxo de dados

```
YAML config --> cli.py (parse) --> MethodConfig (dataclass)
                                        |
Excel .xlsx --> validator.py ---------->|
                                        |
Ecoinvent ZIP --> converter.py -------->|
                                        v
                                  [Pipeline 12 steps]
                                        |
                                        v
                                  output.zip (JSON-LD)
```

### 1.3 Metricas do codigo

| Modulo | Linhas | Classes | Funcoes | Responsabilidade |
|--------|--------|---------|---------|-----------------|
| `__init__.py` | 9 | 0 | 0 | Versao do pacote |
| `schemas.py` | 439 | 8 | 1 | Modelos de dados e serializacao JSON-LD |
| `validator.py` | 177 | 1 | 3 | Validacao de entrada |
| `converter.py` | 512 | 0 | 4 | Pipeline de conversao |
| `cli.py` | 324 | 0 | 5 | Interface de linha de comando |
| **Total** | **1.461** | **9** | **13** | |

### 1.4 Dependencias externas

| Pacote | Versao minima | Finalidade |
|--------|--------------|------------|
| `pandas` | 2.0 | Leitura de planilhas Excel (.xlsx/.xls) |
| `openpyxl` | 3.1 | Motor de leitura do formato .xlsx (usado pelo pandas) |
| `pyyaml` | 6.0 | Parsing de arquivos de configuracao YAML |
| `pytest` | 7.0 | Framework de testes automatizados (dev) |
| `pytest-cov` | 4.0 | Relatorio de cobertura de testes (dev) |

Todas as demais dependencias sao da biblioteca padrao do Python: `json`, `uuid`, `zipfile`, `shutil`, `os`, `pathlib`, `argparse`, `sys`, `dataclasses`.

---

## 2. MODULO schemas.py — MODELOS DE DADOS

### 2.1 Proposito

Define todas as entidades do formato JSON-LD do OpenLCA como dataclasses Python. Cada classe possui um metodo `to_dict()` que produz o dicionario Python correspondente ao JSON final.

### 2.2 Hierarquia de entidades

A hierarquia reflete a estrutura interna do OpenLCA. Cada entidade referencia as inferiores pelo UUID:

```
ImpactMethodDef                    (lcia_methods/{uuid}.json)
  └── ImpactCategoryDef            (lcia_categories/{uuid}.json)
        └── ImpactFactorDef        (array dentro da categoria)
              ├── FlowDef          (flows/{uuid}.json)
              │     └── FlowPropertyDef    (flow_properties/{uuid}.json)
              │           └── UnitGroupDef  (unit_groups/{uuid}.json)
              │                 └── UnitDef (units/{uuid}.json)
              ├── UnitDef (entrada)
              └── FlowPropertyDef (entrada)
```

### 2.3 Detalhamento de cada classe

#### 2.3.1 UnitDef

Representa uma unidade de medida fisica.

```python
@dataclass
class UnitDef:
    name: str                              # Nome da unidade (ex: "kg", "DALY")
    uid: str = field(default_factory=new_uuid)  # UUID v4 gerado automaticamente
```

**Mapeamento para JSON-LD:**
```json
{
  "@type": "Unit",
  "@id": "84152a34-950d-46aa-ac28-2a0e2b386ae0",
  "name": "kg",
  "referenceUnitName": "kg",
  "synonyms": [],
  "internalId": null,
  "default": true
}
```

**Arquivo de saida:** `units/{uid}.json`

---

#### 2.3.2 UnitGroupDef

Agrupa unidades compativeis. O OpenLCA exige que toda unidade pertenca a um grupo.

```python
@dataclass
class UnitGroupDef:
    name: str          # Nome do grupo (ex: "Mass units")
    unit: UnitDef      # Unidade de referencia
    category: str      # Categoria no OpenLCA (ex: "Technical unit groups")
    uid: str           # UUID v4
```

**Campo critico:** `units[0].isReferenceUnit = True` — indica qual unidade e a principal do grupo. Sem este campo, o OpenLCA rejeita a importacao.

**Arquivo de saida:** `unit_groups/{uid}.json`

---

#### 2.3.3 FlowPropertyDef

Define qual grandeza fisica um fluxo mede (massa, volume, energia, etc.).

```python
@dataclass
class FlowPropertyDef:
    name: str                    # Nome da propriedade (ex: "Mass")
    unit_group: UnitGroupDef     # Grupo de unidades associado
    category: str                # Categoria OpenLCA
    flow_property_type: str      # "PHYSICAL_QUANTITY"
    uid: str                     # UUID v4
```

**Relacao com UnitGroup:** A FlowProperty referencia o UnitGroup pelo `@id`. Quando o OpenLCA carrega uma FlowProperty, ele busca o UnitGroup correspondente para determinar as unidades disponiveis.

**Arquivo de saida:** `flow_properties/{uid}.json`

---

#### 2.3.4 FlowDef

Representa um fluxo elementar — uma substancia que cruza a fronteira entre o sistema tecnico e o meio ambiente.

```python
@dataclass
class FlowDef:
    name: str                      # Nome da substancia (ex: "Ammonia")
    category: str                  # Compartimento (ex: "Elementary flows/Emission to air/...")
    flow_property: FlowPropertyDef # Propriedade de fluxo (tipicamente Mass/kg)
    uid: str                       # UUID v4 — pode ser reaproveitado do Ecoinvent
```

**Campo critico:** `flowType = "ELEMENTARY_FLOW"` — distingue de fluxos de produto ou residuo. Todos os fluxos nesta ferramenta sao elementares.

**Regra de deduplicacao:** Dois flows sao considerados iguais se possuem o mesmo `(name, category)`. Localizacoes diferentes (ex: Sao Paulo vs Minas Gerais) compartilham o mesmo flow — a regionalizacao ocorre no nivel do fator de caracterizacao.

**Reuso de UUID:** Se o par `(name, category)` existir na base de referencia Ecoinvent, o UUID original e reaproveitado. Isso garante que o OpenLCA conecte automaticamente o fator ao processo de inventario correspondente.

**Arquivo de saida:** `flows/{uid}.json`

---

#### 2.3.5 ImpactFactorDef

O fator de caracterizacao — o valor numerico que converte emissao em impacto.

```python
@dataclass
class ImpactFactorDef:
    value: float                          # Valor do CF (ex: 0.000579)
    flow: FlowDef                         # Substancia a que se refere
    input_unit: UnitDef                   # Unidade de entrada (ex: kg)
    input_flow_property: FlowPropertyDef  # Propriedade de entrada (ex: Mass)
```

**Mapeamento para JSON-LD:**
```json
{
  "value": 0.0005786934601086489,
  "flow": {
    "@type": "Flow",
    "@id": "9990b51b-7023-4700-bca0-1a32ef921f74",
    "name": "Ammonia",
    "category": "Elementary flows/Emission to air/high population density",
    "flowType": "ELEMENTARY_FLOW",
    "refUnit": "kg"
  },
  "unit": {
    "@type": "Unit",
    "@id": "84152a34-950d-46aa-ac28-2a0e2b386ae0",
    "name": "kg"
  },
  "flowProperty": {
    "@type": "FlowProperty",
    "@id": "da35b4a9-59a1-4347-ad64-c0ba34abd45e",
    "name": "Mass",
    "refUnit": "kg",
    "isRefFlowProperty": true
  }
}
```

**Nao tem arquivo proprio:** Os fatores ficam dentro do array `impactFactors[]` da ImpactCategoryDef.

---

#### 2.3.6 ImpactCategoryDef

Agrupa todos os fatores de um mesmo tipo de impacto.

```python
@dataclass
class ImpactCategoryDef:
    name: str                               # Nome (ex: "particulate matter formation - PMFP")
    description: str                        # Descricao com referencia bibliografica
    ref_unit: str                           # Unidade de referencia (ex: "DALY")
    method_category: str = "endpoint"       # "endpoint" ou "midpoint"
    uid: str                                # UUID v4
    impact_factors: list[ImpactFactorDef]   # Lista de TODOS os fatores
```

**Este e o arquivo mais pesado do pacote.** Para o caso RAICV-Brazil, o JSON da categoria contem 725 entradas no array `impactFactors[]`, resultando em um arquivo de ~200 KB.

**Arquivo de saida:** `lcia_categories/{uid}.json`

---

#### 2.3.7 ImpactMethodDef

Entidade de nivel mais alto — aparece na lista de metodos do OpenLCA.

```python
@dataclass
class ImpactMethodDef:
    name: str                                # Nome (ex: "RAICV-Brazil - PMFP")
    description: str                         # Descricao completa
    categories: list[ImpactCategoryDef]      # Categorias incluidas
    version: str = "1.0"                     # Versao do metodo
    uid: str                                 # UUID v4
```

**Relacao com categorias:** O metodo referencia cada categoria pelo `@id`, mas **nao inclui os fatores** — estes ficam nos arquivos individuais das categorias. O OpenLCA carrega os fatores sob demanda.

**Arquivo de saida:** `lcia_methods/{uid}.json`

---

#### 2.3.8 MethodConfig

Representacao interna da configuracao YAML. Nao gera arquivo JSON — e consumida exclusivamente pelo `converter.py`.

```python
@dataclass
class MethodConfig:
    method_name: str              # Nome do metodo LCIA
    method_description: str       # Descricao com referencia
    category_name: str            # Nome da categoria
    category_description: str     # Descricao da categoria
    category_type: str            # "endpoint" | "midpoint"
    input_unit_name: str          # Unidade de entrada (ex: "kg")
    input_property_name: str      # Propriedade de entrada (ex: "Mass")
    output_unit_name: str         # Unidade de saida (ex: "DALY")
    output_property_name: str     # Propriedade de saida
    excel_path: str               # Caminho para o Excel
    reference_zip: Optional[str]  # ZIP do Ecoinvent (opcional)
    model_zip: Optional[str]      # ZIP modelo (opcional)
    output_zip: str               # Caminho do ZIP de saida
    excel_columns: dict           # Mapeamento de nomes de colunas
```

---

## 3. MODULO validator.py — VALIDACAO DE ENTRADA

### 3.1 Proposito

Garante que os dados de entrada estejam corretos ANTES da conversao (padrao fail-fast). Sem validacao, erros na planilha causariam falhas silenciosas: fatores ignorados, ZIPs vazios ou metodos sem conexao com o inventario.

### 3.2 Funcao validate_excel()

**Assinatura:**
```python
def validate_excel(path: str | Path, required_columns: list[str] | None = None) -> pd.DataFrame
```

**Cadeia de validacoes (nesta ordem):**

| # | Verificacao | Erro se falhar |
|---|------------|----------------|
| 1 | Arquivo existe no disco | `ValidationError: File not found: {path}` |
| 2 | Extensao e .xlsx ou .xls | `ValidationError: Expected .xlsx or .xls, got: {ext}` |
| 3 | pandas consegue ler o arquivo | `ValidationError: Cannot read Excel file: {msg}` |
| 4 | Todas as colunas obrigatorias presentes | `ValidationError: Missing required columns: [...]` |
| 5 | Coluna Factor contem apenas numeros | `ValidationError: Non-numeric values in 'Factor' at rows: [...]` |
| 6 | Coluna Flow nao tem celulas vazias | `ValidationError: Empty flow names at rows: [...]` |

**Retorno:** DataFrame do pandas com os dados validados, pronto para o converter.

### 3.3 Funcao validate_config_paths()

**Assinatura:**
```python
def validate_config_paths(config: dict) -> list[str]
```

**Logica:**
- `files.excel` — OBRIGATORIO. Lanca `ValidationError` se nao existir.
- `files.reference_zip` — Opcional. Retorna warning se nao existir (operara sem reuso de IDs).
- `files.model_zip` — Opcional. Retorna warning se nao existir (criara estrutura do zero).

### 3.4 Funcao print_validation_report()

Imprime resumo estatistico dos dados carregados: numero de linhas, substancias unicas, compartimentos, localizacoes, unidade e faixa de valores dos fatores.

---

## 4. MODULO converter.py — MOTOR DE CONVERSAO

### 4.1 Proposito

Orquestra o pipeline completo de 12 etapas que transforma uma planilha Excel em um pacote ZIP importavel pelo OpenLCA.

### 4.2 Funcoes auxiliares

#### 4.2.1 _write_json(directory, uid, data)

Escreve `{uid}.json` em um diretorio. Usa `indent=2` para legibilidade e `ensure_ascii=False` para suportar caracteres acentuados.

#### 4.2.2 _load_reference_flows(ref_zip)

**Entrada:** Caminho para um ZIP ou diretorio contendo flows de referencia.

**Algoritmo:**
1. Verifica se o argumento e um diretorio ou ZIP
2. Se ZIP: extrai para pasta temporaria `_ref_temp_{PID}/`
3. Busca a pasta `flows/` — primeiro na raiz, depois recursivamente via `rglob("flows")`
4. Para cada arquivo JSON na pasta `flows/`:
   - Verifica se `@type == "Flow"`
   - Extrai `(name, category)` e `@id`
   - Armazena no dicionario com `setdefault` (primeiro encontrado prevalece)
5. Limpa pasta temporaria no bloco `finally`

**Saida:** `dict[(str, str), str]` mapeando `(nome, categoria) -> UUID`

**Tratamento de ZIPs com subpasta:** Se o ZIP foi criado a partir de um diretorio (ex: `zip -r Base-Ecoinvent.zip Base-Ecoinvent/`), a pasta `flows/` estara em `Base-Ecoinvent/flows/` em vez de `flows/`. A busca recursiva com `rglob` resolve isso.

#### 4.2.3 _extract_model_base(model_zip, temp_dir)

**Entrada:** Caminho para um ZIP ou diretorio modelo.

**Algoritmo:**
1. Se diretorio: copia conteudo para `temp_dir`
2. Se ZIP: extrai para `temp_dir`
3. Deteccao de wrapper: se a extracao resultou em uma unica subpasta com `openlca.json`, move o conteudo para a raiz de `temp_dir` e remove a subpasta

### 4.3 Funcao principal: convert(config)

**Assinatura:**
```python
def convert(config: MethodConfig) -> Path
```

**Pipeline detalhado (12 etapas):**

---

**Step 1 — Extrair modelo base (opcional)**

Chama `_extract_model_base()`. Se `model_zip` e `None`, pula silenciosamente. A estrutura base fornece pastas pre-criadas e o manifesto `openlca.json`.

---

**Step 2 — Carregar IDs de referencia (opcional)**

Chama `_load_reference_flows()`. Retorna um dicionario `(nome, categoria) -> UUID` com os flows existentes na base Ecoinvent. Se `reference_zip` e `None`, retorna dicionario vazio.

---

**Step 3 — Ler e validar Excel**

Chama `validate_excel()` com as colunas mapeadas no config. Retorna um DataFrame do pandas. A validacao e executada ANTES de qualquer criacao de arquivo (fail-fast).

---

**Step 4 — Criar unidades de entrada**

Instancia a cadeia `UnitDef -> UnitGroupDef -> FlowPropertyDef` para a unidade de entrada (tipicamente kg/Mass). Cada entidade recebe um UUID v4 novo.

---

**Step 5 — Criar unidades de saida**

Mesma cadeia para a unidade de impacto (ex: DALY/"Impact on human health"). A `category` do UnitGroupDef e FlowPropertyDef varia conforme o tipo:
- endpoint: `"Impact category indicators"`
- midpoint: `"Technical unit groups"` / `"Technical flow properties"`

---

**Step 6 — Escrever JSONs de suporte**

Cria (ou recria) as 6 pastas obrigatorias e escreve os arquivos JSON das unidades, grupos e propriedades de fluxo. Total: 6 arquivos (2 units + 2 unit_groups + 2 flow_properties).

---

**Step 7 — Criar flows com reuso de IDs**

Para cada par unico `(Flow, Category)` no DataFrame:

```python
flow_id = existing_flows.get((flow_name, category), new_uuid())
```

- Se encontrou no dicionario de referencia: reusa o UUID do Ecoinvent
- Se nao encontrou: gera UUID v4 novo

Escreve `flows/{uuid}.json` para cada flow. O relatorio mostra quantos foram reusados vs novos.

**Complexidade:** O(N) onde N = numero de pares unicos (tipicamente centenas). A busca no dicionario e O(1).

---

**Step 8 — Construir mapa completo**

Expande o mapa do Step 7 para incluir localizacao: `(Flow, Category, Location) -> UUID`. Multiplas localizacoes apontam para o MESMO UUID de flow (a regionalizacao esta no fator, nao no flow).

---

**Step 9 — Montar categoria de impacto**

Itera sobre TODAS as linhas do DataFrame. Para cada linha:
1. Busca o UUID no mapa do Step 8
2. Cria um `ImpactFactorDef` com o valor, flow, unidade e propriedade
3. Adiciona ao array `impact_factors[]` da `ImpactCategoryDef`

Fatores cujo flow nao foi encontrado no mapa sao contados como `skipped` e reportados.

Escreve `lcia_categories/{uuid}.json` com o array completo de fatores.

---

**Step 10 — Criar metodo LCIA**

Instancia `ImpactMethodDef` referenciando a categoria do Step 9. Escreve `lcia_methods/{uuid}.json`.

---

**Step 11 — Escrever manifesto**

Cria `openlca.json` na raiz com `{"schemaVersion": 2}`. Este arquivo e obrigatorio — sem ele, o OpenLCA nao reconhece o pacote.

---

**Step 12 — Empacotar em ZIP**

Percorre recursivamente `temp_dir` com `os.walk()` e adiciona cada arquivo ao ZIP com `zipfile.ZIP_DEFLATED`. O `arcname` (caminho dentro do ZIP) e calculado com `Path.relative_to()` para manter a estrutura de pastas.

Apos empacotamento, conta os arquivos no ZIP para o relatorio.

---

**Limpeza:** O bloco `finally` garante que `temp_dir` seja removido mesmo em caso de excecao. A pasta usa `os.getpid()` no nome para evitar colisoes entre execucoes paralelas.

---

## 5. MODULO cli.py — INTERFACE DE LINHA DE COMANDO

### 5.1 Proposito

Ponto de entrada do programa. Interpreta argumentos da linha de comando via `argparse` e despacha para a funcao correspondente.

### 5.2 Comandos

| Comando | Funcao | Descricao |
|---------|--------|-----------|
| `olca-cf convert {config}` | `cmd_convert()` | Executa pipeline completo |
| `olca-cf validate {excel}` | `cmd_validate()` | Valida planilha sem converter |
| `olca-cf init [-o path]` | `cmd_init()` | Gera template YAML |
| `olca-cf --version` | argparse built-in | Mostra versao |
| `olca-cf --help` | argparse built-in | Mostra ajuda |

### 5.3 Funcao _load_config()

Faz o parsing do YAML e retorna um `MethodConfig`. Resolve caminhos relativos com base no diretorio do arquivo config:

```python
def resolve(p):
    if p is None: return None
    pp = Path(p)
    if not pp.is_absolute():
        pp = config_dir / pp   # Resolve relativo ao dir do config
    return str(pp)
```

Isso permite que o config use caminhos como `"../examples/data.xlsx"` e funcione independentemente de onde o usuario execute o comando.

### 5.4 Funcao cmd_convert()

1. Carrega config via `_load_config()`
2. Mostra resumo (metodo, categoria, unidades, Excel)
3. Valida caminhos via `validate_config_paths()` (usando paths ja resolvidos)
4. Chama `convert(config)`
5. Exibe resultado ou erro

### 5.5 Funcao cmd_init()

Gera um dicionario Python com a estrutura do template e serializa como YAML via `yaml.dump()`. Protege contra sobrescrita acidental (requer `--force`).

---

## 6. FORMATO DE SAIDA — PACOTE ZIP

### 6.1 Estrutura completa

```
output.zip
├── openlca.json                         # Manifesto obrigatorio
├── units/
│   ├── {uuid-input-unit}.json           # Unidade de entrada (ex: kg)
│   └── {uuid-output-unit}.json          # Unidade de saida (ex: DALY)
├── unit_groups/
│   ├── {uuid-input-group}.json          # Grupo da unidade de entrada
│   └── {uuid-output-group}.json         # Grupo da unidade de saida
├── flow_properties/
│   ├── {uuid-input-property}.json       # Propriedade de entrada (ex: Mass)
│   └── {uuid-output-property}.json      # Propriedade de saida (ex: Impact)
├── flows/
│   ├── {uuid-flow-1}.json               # 1 arquivo por (substancia, compartimento)
│   ├── {uuid-flow-2}.json
│   └── ... (centenas de arquivos)
├── lcia_categories/
│   └── {uuid-category}.json             # Categoria com array impactFactors[]
└── lcia_methods/
    └── {uuid-method}.json               # Metodo referenciando a categoria
```

### 6.2 Encadeamento de UUIDs

```
ImpactMethod.impactCategories[0].@id ──────> ImpactCategory.@id
ImpactCategory.impactFactors[i].flow.@id ──> Flow.@id
ImpactCategory.impactFactors[i].unit.@id ──> Unit.@id (entrada)
Flow.flowProperties[0].flowProperty.@id ───> FlowProperty.@id
FlowProperty.unitGroup.@id ────────────────> UnitGroup.@id
UnitGroup.units[0].@id ───────────────────-> Unit.@id
```

Se qualquer referencia apontar para um UUID que nao existe no pacote, o OpenLCA ignora silenciosamente a entidade. Este e o erro mais comum e dificil de diagnosticar em pacotes JSON-LD manuais — e a razao pela qual a ferramenta gera todos os UUIDs de forma coordenada.

### 6.3 Manifesto openlca.json

```json
{"schemaVersion": 2}
```

Deve estar na raiz do ZIP, com exatamente este nome. O `schemaVersion` indica a versao do formato JSON-LD. A versao 2 e compativel com OpenLCA 2.x.

---

## 7. MECANISMO DE REUSO DE UUIDs

### 7.1 Problema

O OpenLCA conecta fatores de caracterizacao a processos de inventario **por UUID**, nao por nome. Se um metodo LCIA usa o UUID `aaaa-bbbb` para "Ammonia" e o Ecoinvent usa `9990-b51b` para a mesma substancia, os fatores nao serao aplicados.

### 7.2 Solucao

A ferramenta carrega os UUIDs de uma base de referencia (tipicamente uma exportacao JSON-LD do Ecoinvent) e os reutiliza ao criar os flows do metodo.

### 7.3 Algoritmo de matching

```
Para cada par (nome, categoria) unico na planilha:
    1. Buscar (nome, categoria) no dicionario de referencia
    2. Se encontrado → usar UUID da referencia
    3. Se nao encontrado → gerar UUID v4 novo
    4. Escrever flows/{uuid}.json
```

O matching e **case-sensitive** e requer correspondencia **exata** em ambos os campos. Nao ha normalizacao de nomes (por design — nomes no Ecoinvent sao padronizados).

### 7.4 Busca recursiva em ZIPs com subpasta

ZIPs criados com `zip -r Base-Ecoinvent.zip Base-Ecoinvent/` resultam em `Base-Ecoinvent/flows/` em vez de `flows/` na raiz. A funcao `_load_reference_flows()` trata isso com busca recursiva:

```python
flows_dir = search_root / "flows"
if not flows_dir.is_dir():
    for candidate in search_root.rglob("flows"):
        if candidate.is_dir() and any(candidate.glob("*.json")):
            flows_dir = candidate
            break
```

---

## 8. SUITE DE TESTES

### 8.1 Organizacao

| Arquivo | Testes | Cobertura |
|---------|--------|-----------|
| `test_schemas.py` | 6 | 100% do schemas.py |
| `test_validator.py` | 6 | 59% do validator.py |
| `test_converter.py` | 8 | 77% do converter.py |
| `test_cli.py` | 3 | Via subprocess |
| **Total** | **23** | **58% global** |

### 8.2 Testes de schemas (test_schemas.py)

| Teste | Verifica |
|-------|----------|
| `test_unit_group_to_dict` | UnitGroup serializa corretamente com unit e isReferenceUnit |
| `test_flow_property_to_dict` | FlowProperty referencia UnitGroup pelo @id |
| `test_flow_def_to_dict` | Flow tem flowType=ELEMENTARY_FLOW e flowProperties[] |
| `test_impact_factor_to_dict` | Fator tem value, flow.@id, unit.@id, flowProperty.@id |
| `test_impact_category_to_dict` | Categoria tem refUnit e impactFactors=[] (vazio) |
| `test_impact_method_to_dict` | Metodo referencia categorias pelo @id |

### 8.3 Testes de validacao (test_validator.py)

| Teste | Verifica |
|-------|----------|
| `test_validate_valid_file` | Arquivo valido retorna DataFrame com 3 linhas |
| `test_validate_file_not_found` | Arquivo inexistente lanca ValidationError |
| `test_validate_wrong_extension` | Extensao .csv lanca ValidationError |
| `test_validate_missing_columns` | Colunas faltantes listadas na mensagem de erro |
| `test_validate_non_numeric_factor` | Texto na coluna Factor lanca ValidationError |
| `test_validate_empty_flow_name` | Nome de flow vazio lanca ValidationError |

### 8.4 Testes de conversao (test_converter.py)

| Teste | Verifica |
|-------|----------|
| `test_convert_produces_zip` | Arquivo .zip e criado |
| `test_zip_contains_required_structure` | 6 pastas obrigatorias + openlca.json presentes |
| `test_flows_have_correct_structure` | JSONs de flow tem @type, flowType, @id, flowProperties |
| `test_impact_factors_count` | Numero de fatores = numero de linhas do Excel |
| `test_method_references_category` | Method.impactCategories[0].@id == Category.@id |
| `test_unique_flows_deduplication` | Flows deduplicados por (name, category) |
| `test_midpoint_config` | refUnit e category corretos para midpoint |
| `test_reference_zip_id_reuse` | UUID conhecido do Ecoinvent aparece no flow gerado |

### 8.5 Testes de CLI (test_cli.py)

| Teste | Verifica |
|-------|----------|
| `test_cli_help` | `--help` retorna exit code 0 e mostra "convert", "validate", "init" |
| `test_cli_version` | `--version` retorna "1.0.0" |
| `test_cli_init` | Template YAML gerado contem secoes method, category, units, files |

### 8.6 Execucao

```bash
# Testes simples
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=olca_cf_converter --cov-report=term-missing

# Resultado esperado: 23 passed
```

---

## 9. DECISOES DE DESIGN

### 9.1 Por que dataclasses e nao dicionarios?

Dataclasses fornecem tipagem estatica, auto-complete em IDEs, e garantem que campos obrigatorios nao sejam esquecidos em tempo de construcao. O custo e minimo (1 metodo `to_dict()` por classe) e o beneficio em legibilidade e manutencao e significativo.

### 9.2 Por que YAML e nao JSON para configuracao?

YAML suporta comentarios (essencial para usuarios nao-programadores), e mais legivel que JSON para estruturas simples, e e o padrao em ferramentas cientificas. A dependencia adicional (`pyyaml`) e leve.

### 9.3 Por que nao usar o pacote olca-schema?

O `olca-schema` oficial da GreenDelta e uma opcao, mas adiciona uma dependencia pesada para um caso de uso simples (gerar JSONs estaticos). A abordagem com dataclasses proprias e mais leve (zero dependencias externas alem de pandas), transparente (todo o formato visivel no codigo) e educativa.

### 9.4 Por que PID nas pastas temporarias?

Evita colisoes se dois processos de conversao rodarem simultaneamente (ex: em um pipeline de CI/CD ou num script de batch que processa multiplos metodos em paralelo).

### 9.5 Por que fail-fast na validacao?

A conversao cria centenas de arquivos. Se a validacao fosse feita durante a conversao, um erro na linha 500 do Excel resultaria em um pacote parcialmente gerado. A validacao antecipada garante que nenhum arquivo e criado se os dados de entrada forem invalidos.

### 9.6 Por que deduplicar flows por (nome, categoria) e nao por (nome, categoria, localizacao)?

No modelo de dados do OpenLCA, a regionalizacao ocorre no nivel do fator de caracterizacao, nao do fluxo elementar. "Ammonia emitida ao ar em Sao Paulo" e "Ammonia emitida ao ar em Minas Gerais" sao o MESMO flow com fatores de caracterizacao DIFERENTES. Criar flows separados por localizacao quebraria a compatibilidade com o Ecoinvent, que possui um unico flow para "Ammonia/air".
