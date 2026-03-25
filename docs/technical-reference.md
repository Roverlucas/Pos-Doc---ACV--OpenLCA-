# Referencia Tecnica

Documentacao tecnica detalhada do codigo-fonte do `olca-cf-converter`, desenvolvido no ambito do Pos-Doutorado da Dra. Yara de Souza Tadano (UFRJ) na area de Avaliacao de Impacto do Ciclo de Vida. Este documento descreve a arquitetura, os modulos, o pipeline de conversao e o formato de saida.

---

## Indice

1. [Arquitetura Geral](#arquitetura-geral)
2. [Pipeline de Conversao](#pipeline-de-conversao)
3. [Modulos](#modulos)
   - [schemas.py — Modelos de Dados](#schemaspy--modelos-de-dados)
   - [validator.py — Validacao de Entrada](#validatorpy--validacao-de-entrada)
   - [converter.py — Motor de Conversao](#converterpy--motor-de-conversao)
   - [cli.py — Interface de Linha de Comando](#clipy--interface-de-linha-de-comando)
4. [Formato JSON-LD do OpenLCA](#formato-json-ld-do-openlca)
5. [Script Original vs Versao Generica](#script-original-vs-versao-generica)
6. [Decisoes de Design](#decisoes-de-design)

---

## Arquitetura Geral

```
                    +----------------+
                    |   config.yaml  |  <- Configuracao do usuario
                    +-------+--------+
                            |
                            v
                    +-------+--------+
                    |    cli.py      |  <- Parsing de argumentos, orquestracao
                    +-------+--------+
                            |
               +------------+------------+
               |                         |
               v                         v
      +--------+--------+      +--------+--------+
      |  validator.py   |      |  converter.py   |
      |  (valida Excel  |      |  (pipeline de   |
      |   e config)     |      |   conversao)    |
      +--------+--------+      +--------+--------+
               |                         |
               v                         v
      +--------+--------+      +--------+--------+
      |  pandas DataFrame|      |  schemas.py    |
      |  (dados brutos)  |      |  (dataclasses  |
      +-----------------+      |   -> JSON-LD)   |
                               +--------+--------+
                                        |
                                        v
                               +--------+--------+
                               |   output.zip    |
                               |  (pacote OpenLCA|
                               |   importavel)   |
                               +-----------------+
```

**Fluxo de dados:** YAML config -> CLI parser -> Validator (Excel) -> Converter (pipeline 12 steps) -> ZIP output.

Nao ha banco de dados, cache ou estado persistente. Cada execucao e idempotente.

---

## Pipeline de Conversao

O `converter.py` executa 12 passos sequenciais:

| Step | Descricao | Artefato gerado |
|------|-----------|-----------------|
| 1 | Extrair modelo base (opcional) | Pasta temporaria com estrutura |
| 2 | Carregar IDs de referencia (opcional) | Dict `(name, category) -> UUID` |
| 3 | Ler e validar Excel | DataFrame com CFs |
| 4 | Criar unidades de entrada | `units/{uuid}.json` (ex: kg) |
| 5 | Criar unidades de saida | `units/{uuid}.json` (ex: DALY) |
| 6 | Escrever unidades, grupos e propriedades | `unit_groups/`, `flow_properties/` |
| 7 | Criar flows (reusando IDs) | `flows/{uuid}.json` por substancia |
| 8 | Construir mapa de UUIDs | Dict `(name, cat, location) -> UUID` |
| 9 | Criar categoria de impacto com CFs | `lcia_categories/{uuid}.json` |
| 10 | Criar metodo LCIA | `lcia_methods/{uuid}.json` |
| 11 | Escrever manifesto | `openlca.json` |
| 12 | Empacotar em ZIP | Arquivo `.zip` final |

### Diagrama do pipeline

```
Excel (.xlsx)
    |
    v
[Step 3] validate_excel() -----> Erro se invalido
    |
    v
DataFrame (N linhas x 5 colunas)
    |
    +---> [Step 7] Deduplicar por (Flow, Category)
    |         |
    |         +---> Buscar UUID no reference_zip [Step 2]
    |         |         |
    |         |         +---> Encontrado: reusar UUID
    |         |         +---> Nao encontrado: uuid.uuid4()
    |         |
    |         +---> Gerar flows/{uuid}.json
    |
    +---> [Step 8] Mapear (Flow, Category, Location) -> UUID
    |
    +---> [Step 9] Para cada linha do DataFrame:
    |         |
    |         +---> Criar ImpactFactorDef(value, flow_uuid, unit, property)
    |         +---> Adicionar ao array impactFactors[]
    |
    +---> [Step 10] Criar ImpactMethodDef referenciando a categoria
    |
    v
[Step 12] zipfile.ZipFile(output, ZIP_DEFLATED)
    |
    v
output.zip (pronto para OpenLCA)
```

---

## Modulos

### schemas.py — Modelos de Dados

Define as entidades do formato JSON-LD do OpenLCA como dataclasses Python. Cada classe tem um metodo `to_dict()` que gera o JSON final.

#### Hierarquia de entidades

```
ImpactMethodDef
  └── ImpactCategoryDef (1..N)
        └── ImpactFactorDef (1..N)
              ├── FlowDef
              │     └── FlowPropertyDef
              │           └── UnitGroupDef
              │                 └── UnitDef
              ├── UnitDef (input)
              └── FlowPropertyDef (input)
```

#### Classes

| Classe | Campos principais | Responsabilidade |
|--------|-------------------|------------------|
| `UnitDef` | name, uid | Unidade fisica (kg, DALY, m3) |
| `UnitGroupDef` | name, unit, category, uid | Agrupamento de unidades compativeis |
| `FlowPropertyDef` | name, unit_group, category, uid | Propriedade do fluxo (Mass, Volume) |
| `FlowDef` | name, category, flow_property, uid | Fluxo elementar (substancia) |
| `ImpactFactorDef` | value, flow, input_unit, input_flow_property | Fator de caracterizacao (CF) |
| `ImpactCategoryDef` | name, description, ref_unit, impact_factors, uid | Categoria de impacto (PMFP, GWP) |
| `ImpactMethodDef` | name, description, categories, uid | Metodo LCIA completo |
| `MethodConfig` | Todos os parametros do YAML | Configuracao parseada |

#### Geracao de UUIDs

Todos os UUIDs sao gerados via `uuid.uuid4()` (aleatorio, v4). A excecao sao flows que existem no `reference_zip` — esses reutilizam o UUID da base de referencia.

```python
def new_uuid() -> str:
    return str(uuid.uuid4())
```

#### Exemplo de JSON gerado por FlowDef.to_dict()

```json
{
  "@type": "Flow",
  "@id": "9990b51b-7023-4700-bca0-1a32ef921f74",
  "name": "Ammonia",
  "category": "Elementary flows/Emission to air/unspecified",
  "flowType": "ELEMENTARY_FLOW",
  "flowProperties": [{
    "@type": "FlowPropertyFactor",
    "isRefFlowProperty": true,
    "conversionFactor": 1.0,
    "flowProperty": {
      "@type": "FlowProperty",
      "@id": "da35b4a9-...",
      "name": "Mass",
      "refUnit": "kg"
    }
  }]
}
```

---

### validator.py — Validacao de Entrada

Modulo responsavel por validar a planilha Excel e os caminhos de arquivo do config YAML antes da conversao.

#### Funcoes

| Funcao | Entrada | Saida | Erros |
|--------|---------|-------|-------|
| `validate_excel(path, required_columns)` | Path do .xlsx, lista de colunas | DataFrame validado | `ValidationError` se invalido |
| `validate_config_paths(config)` | Dict do YAML parseado | Lista de warnings (str) | `ValidationError` se Excel nao existe |
| `print_validation_report(df)` | DataFrame | Print no terminal | Nenhum |

#### Verificacoes realizadas por validate_excel()

1. **Arquivo existe** — `Path.exists()`
2. **Extensao correta** — `.xlsx` ou `.xls`
3. **Leitura sem erros** — `pd.read_excel()` nao lanca excecao
4. **Colunas obrigatorias** — todas as colunas esperadas presentes
5. **Fatores numericos** — coluna Factor contem apenas `int` ou `float`
6. **Flows nao vazios** — coluna Flow sem valores nulos ou strings vazias

#### Mapeamento de colunas customizavel

Os nomes das colunas sao configuraveis no YAML via a secao `columns:`. O default e:

```yaml
columns:
  flow: Flow
  category: Category
  factor: Factor
  unit: Unit
  location: Location
```

Se sua planilha usa nomes diferentes (ex: "Substance" em vez de "Flow"), basta alterar no YAML.

---

### converter.py — Motor de Conversao

Contem a funcao principal `convert(config: MethodConfig) -> Path` e funcoes auxiliares.

#### Funcoes internas

| Funcao | Descricao |
|--------|-----------|
| `_write_json(directory, uid, data)` | Escreve `{uid}.json` em um diretorio |
| `_load_reference_flows(ref_zip)` | Le flows do ZIP de referencia, retorna dict de IDs |
| `_extract_model_base(model_zip, temp_dir)` | Extrai estrutura base do modelo |
| `convert(config)` | Pipeline completo (12 steps) |

#### Logica de reuso de IDs (Step 7)

```python
# Para cada (flow_name, category) unico na planilha:
flow_id = existing_flows.get((flow_name, category), new_uuid())
#                         ^                           ^
#                         |                           |
#               Busca no reference_zip     Gera novo se nao encontrado
```

O match e feito por **tupla exata** `(name, category)`. Isso significa:
- "Ammonia" + "Elementary flows/Emission to air/unspecified" -> match
- "Ammonia" + "Elementary flows/Emission to air/high population density" -> match diferente
- "ammonia" (minusculo) + mesmo path -> **nao faz match** (case-sensitive)

#### Deduplicacao de flows

Uma mesma substancia pode aparecer multiplas vezes na planilha (com diferentes localizacoes). A ferramenta deduplica por `(Flow, Category)`:

```
Excel: 725 linhas (ex: Ammonia aparece 28 vezes, uma por estado)
Flows gerados: ~145 arquivos (um por substancia+compartimento unico)
Fatores no JSON: 725 (todos, referenciando o UUID do flow correspondente)
```

#### Gerenciamento de pastas temporarias

O pipeline usa uma pasta temporaria `_olca_build_{pid}/` que e **sempre removida** no bloco `finally`, mesmo em caso de erro. O PID garante que execucoes paralelas nao colidem.

---

### cli.py — Interface de Linha de Comando

Implementa 3 comandos via `argparse`:

| Comando | Descricao | Exemplo |
|---------|-----------|---------|
| `convert` | Executa o pipeline completo | `olca-cf convert config.yaml` |
| `validate` | Valida um arquivo Excel | `olca-cf validate data.xlsx` |
| `init` | Gera template de config YAML | `olca-cf init -o meu.yaml` |

#### Resolucao de caminhos

Todos os caminhos no YAML sao resolvidos **relativamente ao diretorio do config**. Exemplo:

```yaml
# Se o config esta em /projeto/configs/meu.yaml
files:
  excel: "../data/fatores.xlsx"  # Resolve para /projeto/data/fatores.xlsx
```

Caminhos absolutos sao usados diretamente.

#### Entrada e saida

- **Entrada:** argumento de linha de comando -> YAML parseado -> MethodConfig
- **Saida:** prints no terminal (progresso) + arquivo ZIP no disco

---

## Formato JSON-LD do OpenLCA

O OpenLCA importa pacotes no formato JSON-LD (schema v2). A estrutura minima para um metodo LCIA e:

### Manifesto (openlca.json)

```json
{"schemaVersion": 2}
```

Deve estar na **raiz** do ZIP. Sem este arquivo, o OpenLCA rejeita a importacao.

### Encadeamento de entidades

```
ImpactMethod
  |
  +--references--> ImpactCategory (por @id)
                     |
                     +--contains--> ImpactFactor[]
                                      |
                                      +--references--> Flow (por @id)
                                      +--references--> Unit (por @id)
                                      +--references--> FlowProperty (por @id)
```

Cada `@id` deve corresponder a um arquivo `{@id}.json` na pasta correspondente do ZIP. Se um `@id` referenciado nao existir, o OpenLCA ignora silenciosamente o fator.

### Tipos de entidade por pasta

| Pasta | @type | Quantidade tipica |
|-------|-------|-------------------|
| `units/` | Unit | 2 (entrada + saida) |
| `unit_groups/` | UnitGroup | 2 |
| `flow_properties/` | FlowProperty | 2 |
| `flows/` | Flow | Centenas (1 por substancia+compartimento) |
| `lcia_categories/` | ImpactCategory | 1 por categoria |
| `lcia_methods/` | ImpactMethod | 1 |

---

## Script Original vs Versao Generica

O `olca-cf-converter` foi generalizado a partir de um script monolitico (`FINAL-correto-reused-ids.py`) desenvolvido especificamente para o caso RAICV-Brazil.

### O que mudou

| Aspecto | Script original | Versao generica |
|---------|----------------|-----------------|
| Configuracao | Hardcoded no `.py` (nomes, paths, unidades) | Arquivo YAML externo |
| Unidade de saida | Apenas DALY | Qualquer (DALY, kg CO2-Eq, CTUe, etc.) |
| Tipo de categoria | Apenas endpoint | Endpoint ou midpoint |
| Nomes de colunas | Fixos (Flow, Category, Factor, Unit, Location) | Configuraveis no YAML |
| Validacao | Nenhuma | Validacao completa de Excel e config |
| Interface | Editar e rodar o `.py` | CLI com 3 comandos |
| Testes | Nenhum | 23 testes automatizados |
| Reuso de IDs | Funcional mas acoplado | Modular, aceita ZIP ou diretorio |
| Estrutura | 1 arquivo, 330 linhas | 4 modulos, ~700 linhas |
| Erro handling | Minimo (prints) | Exceptions tipadas, mensagens claras |
| Documentacao | Comentarios no codigo | README + 4 docs + docstrings |

### O que foi preservado

A logica central de conversao e identica ao script original:
- Formato JSON-LD gerado e o mesmo
- Logica de deduplicacao por (name, category) e a mesma
- Logica de reuso de IDs por (name, category) e a mesma
- Estrutura do ZIP final e a mesma
- Compatibilidade com OpenLCA schema v2

### Script original preservado

O script original (`FINAL-correto-reused-ids.py`) esta documentado em `docs/original-script.md` para referencia historica e rastreabilidade.

---

## Decisoes de Design

### Por que YAML e nao JSON para config?

YAML suporta comentarios, e mais legivel para pesquisadores nao-programadores, e e o padrao em ferramentas cientificas. JSON seria uma alternativa valida, mas YAML facilita a documentacao inline.

### Por que dataclasses e nao dicts?

Dataclasses fornecem type safety, auto-complete em IDEs, e garantem que campos obrigatorios nao sejam esquecidos. O metodo `to_dict()` converte para o formato final somente na hora de escrever o JSON.

### Por que nao usar olca-ipc ou olca-schema?

O pacote `olca-schema` oficial do GreenDelta e uma opcao, mas adiciona uma dependencia pesada para um caso de uso simples (gerar JSONs estaticos). A abordagem com dataclasses proprias e mais leve, transparente e sem dependencias externas alem de pandas/openpyxl/pyyaml.

### Por que deduplicar flows por (name, category)?

No Ecoinvent, a mesma substancia em compartimentos diferentes (ex: "Ammonia" emitida ao ar vs ao solo) sao flows distintos com UUIDs distintos. Porem, a mesma substancia no mesmo compartimento em localizacoes diferentes (ex: "Ammonia/air/unspecified" em SP vs RJ) e o **mesmo flow** — a regionalizacao acontece no nivel do fator de caracterizacao, nao do flow.

### Por que PID nas pastas temporarias?

Evita colisoes se dois processos de conversao rodarem simultaneamente (ex: em CI/CD ou num script de batch).
