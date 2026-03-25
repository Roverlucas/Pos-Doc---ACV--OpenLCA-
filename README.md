# olca-cf-converter

**Converta planilhas de Fatores de Caracterização em pacotes JSON-LD importaveis no OpenLCA.**

Ferramenta open-source para pesquisadores de Analise de Ciclo de Vida (ACV/LCA) que desenvolvem metodos LCIA regionalizados ou adaptados. Automatiza a conversao de uma planilha Excel com fatores de caracterizacao (CFs) em um pacote ZIP pronto para importar no [OpenLCA](https://www.openlca.org/).

---

## Sobre o Projeto

Este repositorio faz parte do projeto de **Pos-Doutorado da Dra. Yara de Souza Tadano**, na area de Analise de Ciclo de Vida (ACV). O trabalho visa criar ferramentas abertas e reprodutiveis para facilitar a integracao de novos metodos de avaliacao de impacto ambiental no software OpenLCA, contribuindo para a democratizacao e padronizacao de metodos LCIA desenvolvidos pela comunidade cientifica brasileira e internacional.

O caso de uso original foi construido a partir dos fatores de caracterizacao desenvolvidos pela **Dra. Gabriela Giusti** (UFSCar, 2025), no contexto do metodo RAICV-Brazil para formacao de material particulado (PMFP), com fatores regionalizados para todos os estados brasileiros.

---

## O Problema

Pesquisadores que desenvolvem novos fatores de caracterizacao (em teses, dissertacoes ou artigos) enfrentam um gargalo operacional: converter centenas ou milhares de fatores em arquivos JSON-LD compativeis com o OpenLCA. Esse processo manual e:

- **Tedioso** — cada substancia (flow), unidade, grupo de unidades e fator precisa de um arquivo JSON separado, com UUIDs consistentes entre si
- **Propenso a erros** — um UUID errado em um unico arquivo quebra o encadeamento e os fatores nao sao aplicados ao inventario
- **Incompativel sem cuidado** — se os UUIDs nao coincidirem com os da base Ecoinvent, o metodo importado nao se conecta aos processos do inventario existente
- **Nao documentado** — o formato JSON-LD do OpenLCA (schema v2) tem nuances nao cobertas na documentacao oficial, especialmente para LCIA regionalizados

O resultado e que muitos metodos LCIA publicados em teses e artigos nunca chegam a ser integrados no OpenLCA, ficando restritos a tabelas em PDF.

---

## A Solucao

O `olca-cf-converter` resolve todo o pipeline com **uma linha de comando**:

```bash
olca-cf convert meu-metodo.yaml
```

A ferramenta le uma planilha Excel padronizada, aplica a configuracao definida em um arquivo YAML, reutiliza IDs de bases de referencia (Ecoinvent), e gera um pacote ZIP pronto para importacao no OpenLCA.

---

## Funcionalidades

| Funcionalidade | Descricao |
|----------------|-----------|
| **Qualquer categoria de impacto** | DALY, kg CO2-Eq, mol H+-Eq, CTUe, PDF*m2*yr, etc. |
| **Endpoint e midpoint** | Ambos os tipos de categoria sao suportados |
| **Reuso de IDs Ecoinvent** | Mantém compatibilidade com bancos de inventario existentes |
| **Regionalizacao** | Suporta fatores por localizacao (pais, estado, regiao) |
| **Validacao de entrada** | Verifica o Excel antes de converter (colunas, tipos, vazios) |
| **Configuracao via YAML** | Sem necessidade de editar codigo Python |
| **CLI simples** | Tres comandos: `convert`, `validate`, `init` |
| **Mapeamento de colunas** | Nomes de colunas configuraveis no YAML |
| **Instalavel via pip** | Pacote Python padrao com `pyproject.toml` |

---

## Casos de Uso

### 1. Teses e Dissertacoes com novos CFs

Um doutorando que desenvolveu fatores de caracterizacao regionalizados para o Brasil (por exemplo, para material particulado, eutrofizacao ou toxicidade humana) pode usar esta ferramenta para empacotar seus fatores e disponibiliza-los para a comunidade via OpenLCA, sem necessidade de programacao.

### 2. Grupos de pesquisa que publicam metodos LCIA

Grupos que desenvolvem metodos LCIA novos ou adaptados (ex: RAICV-Brazil, LC-Impact, IMPACT World+) podem usar a ferramenta para gerar pacotes de distribuicao dos seus metodos, garantindo compatibilidade com Ecoinvent e outros bancos de dados.

### 3. Artigos cientificos com material suplementar

Autores que publicam artigos com novos CFs podem incluir o config YAML e a planilha Excel como material suplementar, permitindo que qualquer leitor reproduza o pacote OpenLCA em minutos.

### 4. Empresas e consultorias

Organizacoes que desenvolvem fatores de caracterizacao proprietarios ou adaptados para contextos regionais podem automatizar a integracao desses fatores em suas bases OpenLCA internas.

### 5. Ensino e capacitacao

Professores de ACV podem usar a ferramenta como material didatico para demonstrar a estrutura interna de metodos LCIA no OpenLCA e como fatores de caracterizacao se conectam a fluxos elementares.

---

## Inicio Rapido

### 1. Instalar

```bash
# Clonar o repositorio
git clone https://github.com/Roverlucas/Pos-Doc---ACV--OpenLCA-.git
cd Pos-Doc---ACV--OpenLCA-

# Criar ambiente virtual e instalar
python3 -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

pip install -e ".[dev]"
```

**Requisitos:** Python 3.10 ou superior.

### 2. Preparar sua planilha Excel

Crie um arquivo `.xlsx` com estas colunas (nomes configuraveis):

| Flow | Category | Factor | Unit | Location |
|------|----------|--------|------|----------|
| Ammonia | Elementary flows/Emission to air/unspecified | 0.000579 | DALY | Brazil |
| Ammonia | Elementary flows/Emission to air/high population density | 0.000579 | DALY | Brazil, Sao Paulo |
| Nitrogen oxides | Elementary flows/Emission to air/unspecified | 0.001230 | DALY | Brazil |

**O que cada coluna representa:**

| Coluna | Descricao | Exemplo |
|--------|-----------|---------|
| `Flow` | Nome da substancia emitida. Deve coincidir com os nomes do Ecoinvent para reuso de IDs. | Ammonia, Nitrogen oxides, Sulfur dioxide |
| `Category` | Caminho completo do compartimento ambiental no OpenLCA. Define para onde a emissao vai. | Elementary flows/Emission to air/high population density |
| `Factor` | Valor numerico do fator de caracterizacao. Expressa o impacto por unidade de emissao. | 0.000579 |
| `Unit` | Unidade de saida (informativo — a unidade real vem do config YAML). | DALY, kg CO2-Eq |
| `Location` | Localizacao geografica. Permite fatores regionalizados por pais, estado ou regiao. | Brazil, Brazil, Minas Gerais |

### 3. Criar config YAML

```bash
# Gerar template automaticamente
olca-cf init -o meu-metodo.yaml
```

Edite o arquivo gerado com os dados do seu metodo:

```yaml
method:
  name: "Meu Metodo LCIA"
  description: "Descricao com referencia bibliografica completa."

category:
  name: "minha categoria de impacto"
  description: "Fatores de caracterizacao para..."
  type: endpoint              # endpoint ou midpoint

units:
  input:
    name: kg                  # unidade de entrada (massa emitida)
    property: Mass
  output:
    name: DALY                # unidade de impacto
    property: "Impact on human health"

files:
  excel: "meus-fatores.xlsx"
  reference_zip: "Base-Ecoinvent.zip"   # opcional: para reuso de IDs
  model_zip: null                        # opcional: estrutura base
  output_zip: "Meu-Metodo-FINAL.zip"

# Mapeamento de colunas (opcional — altere se sua planilha usa nomes diferentes)
columns:
  flow: Flow
  category: Category
  factor: Factor
  unit: Unit
  location: Location
```

### 4. Converter

```bash
olca-cf convert meu-metodo.yaml
```

Saida esperada:
```
============================================================
  olca-cf-converter v1.0.0
============================================================

  Method:   Meu Metodo LCIA
  Category: minha categoria de impacto
  Units:    kg -> DALY
  Excel:    meus-fatores.xlsx

  Converting...

  ✓ Loaded 725 characterization factors from Excel
  ✓ Loaded 1842 reference flow IDs
  ✓ Flows: 680 reused IDs + 45 new = 725 total
  ✓ Impact category: 725 factors
  ✓ Method: Meu Metodo LCIA
  ✓ Output: Meu-Metodo-FINAL.zip (734 files)

  Done! Import this file into OpenLCA:
     Meu-Metodo-FINAL.zip

  OpenLCA: File -> Import -> JSON-LD -> select the ZIP
```

### 5. Importar no OpenLCA

1. Abra o OpenLCA com um banco de dados ativo
2. Va em **File -> Import**
3. Selecione **Linked Data (JSON-LD)**
4. Navegue ate o arquivo `.zip` gerado
5. Clique em **Finish**

O metodo aparecera em **Impact assessment methods** no navegador do OpenLCA.

---

## Validacao

Antes de converter, valide sua planilha:

```bash
olca-cf validate meus-fatores.xlsx
```

O que e verificado:
- Formato do arquivo (.xlsx ou .xls)
- Presenca de todas as colunas obrigatorias
- Valores numericos na coluna Factor
- Nomes de flows nao vazios

---

## Exemplos de Configuracao

### Mudanca Climatica (GWP100 - midpoint)

```yaml
method:
  name: "GWP Regionalizado Brasil"
  description: "Potenciais de aquecimento global adaptados para o contexto brasileiro."
category:
  name: "climate change - GWP100"
  description: "Global warming potential over 100 years."
  type: midpoint
units:
  input: { name: kg, property: Mass }
  output: { name: "kg CO2-Eq", property: "Global warming potential" }
files:
  excel: "gwp-factors.xlsx"
  reference_zip: "Base-Ecoinvent.zip"
  output_zip: "GWP-Brasil-FINAL.zip"
```

### Acidificacao (midpoint)

```yaml
method:
  name: "Acidificacao Regional"
  description: "Potenciais de acidificacao regionalizados."
category:
  name: "terrestrial acidification - TAP"
  description: "Terrestrial acidification potential."
  type: midpoint
units:
  input: { name: kg, property: Mass }
  output: { name: "mol H+-Eq", property: "Acidification potential" }
```

### Ecotoxicidade Aquatica (midpoint)

```yaml
method:
  name: "Ecotoxicidade Agua Doce"
  description: "Fatores de ecotoxicidade para agua doce."
category:
  name: "freshwater ecotoxicity - FETPinf"
  type: midpoint
units:
  input: { name: kg, property: Mass }
  output: { name: "CTUe", property: "Comparative toxic unit for ecosystems" }
```

### Uso do Solo (endpoint)

```yaml
method:
  name: "Land Use Biodiversity"
  description: "Impacto na biodiversidade por uso do solo."
category:
  name: "land use - species loss"
  type: endpoint
units:
  input: { name: "m2*yr", property: "Area*time" }
  output: { name: "PDF*m2*yr", property: "Potentially disappeared fraction" }
```

### Toxicidade Humana (midpoint)

```yaml
method:
  name: "Human Toxicity - Cancer"
  description: "Fatores de toxicidade humana cancerigena."
category:
  name: "human toxicity - HTPc"
  type: midpoint
units:
  input: { name: kg, property: Mass }
  output: { name: "CTUh", property: "Comparative toxic unit for humans" }
```

Mais exemplos em `configs/`.

---

## Categorias de Impacto Suportadas

A ferramenta e **generica** — funciona com qualquer combinacao de unidade de entrada/saida. Exemplos comuns na literatura:

| Categoria | Tipo | Unidade de Saida | Metodos de referencia |
|-----------|------|------------------|----------------------|
| Mudanca climatica (GWP) | midpoint | kg CO2-Eq | ReCiPe, CML, IMPACT World+ |
| Acidificacao terrestre | midpoint | mol H+-Eq | ReCiPe, IMPACT World+ |
| Eutrofizacao aquatica | midpoint | kg P-Eq | ReCiPe, CML |
| Eutrofizacao marinha | midpoint | kg N-Eq | ReCiPe, CML |
| Formacao de material particulado | endpoint | DALY | RAICV-Brazil, ReCiPe |
| Toxicidade humana (cancer) | midpoint | CTUh | USEtox |
| Toxicidade humana (nao-cancer) | midpoint | CTUh | USEtox |
| Ecotoxicidade aquatica | midpoint | CTUe | USEtox |
| Deplecao de ozonio | midpoint | kg CFC-11-Eq | ReCiPe, CML |
| Formacao de ozonio fotoquimico | midpoint | kg NMVOC-Eq | ReCiPe |
| Uso do solo | endpoint | PDF*m2*yr | ReCiPe, LC-Impact |
| Deplecao de recursos minerais | midpoint | kg Cu-Eq | ReCiPe |
| Radiacao ionizante | midpoint | kBq Co-60-Eq | ReCiPe |
| Uso de agua | midpoint | m3 water-eq | AWARE |

---

## Como Funciona o Reuso de IDs Ecoinvent

No OpenLCA, cada fluxo elementar (substancia) e identificado por um UUID unico. Quando voce importa um metodo LCIA, o OpenLCA conecta os fatores de caracterizacao aos processos do inventario **por UUID** — nao por nome.

Se voce criar UUIDs novos para substancias que ja existem no Ecoinvent, os fatores **nao serao aplicados** aos processos do inventario, mesmo que o nome seja identico.

### Fluxo de matching

```
Sua planilha Excel              Base Ecoinvent (reference_zip)
+-------------------+          +-------------------------------+
| Flow: "Ammonia"   |          | Flow: "Ammonia"               |
| Cat: ".../air/..." |---match->| Cat: ".../air/..."            |
|                   |          | @id: "9990b51b-7023-..."      |
+-------------------+          +-------------------------------+
         |                                  |
         |          reutiliza UUID          |
         v                                  |
+-------------------+                       |
| Flow gerado:      |<---------------------+
| @id: "9990b51b..."| <- mesmo ID = compativel
+-------------------+
```

A ferramenta faz o match usando a **combinacao exata** de:
- Nome do flow (ex: "Ammonia")
- Categoria completa (ex: "Elementary flows/Emission to air/high population density")

Se ambos coincidirem, o UUID e reaproveitado. Caso contrario, um novo UUID e gerado.

### Como obter o reference_zip

**Opcao 1 — Exportar do OpenLCA:**
1. Abra o OpenLCA com o banco de dados Ecoinvent
2. Botao direito no banco -> Export -> JSON-LD Zip
3. Use o ZIP como `reference_zip` na config

**Opcao 2 — Sem reference_zip:**
A ferramenta gera UUIDs novos para todos os flows. O metodo funciona no OpenLCA, mas nao se conecta automaticamente a processos existentes. Sera necessario usar o Flow Mapping do OpenLCA manualmente.

---

## Estrutura do Pacote Gerado

```
Meu-Metodo-FINAL.zip
├── openlca.json              # Manifesto (schemaVersion: 2)
├── units/                    # Definicoes de unidades (kg, DALY, etc.)
│   ├── {uuid-kg}.json
│   └── {uuid-daly}.json
├── unit_groups/              # Grupos de unidades
│   ├── {uuid-mass-group}.json
│   └── {uuid-impact-group}.json
├── flow_properties/          # Propriedades de fluxo (Mass, Impact, etc.)
│   ├── {uuid-mass-prop}.json
│   └── {uuid-impact-prop}.json
├── flows/                    # Fluxos elementares (1 arquivo por substancia+compartimento)
│   ├── {uuid-ammonia-air}.json
│   ├── {uuid-nox-air}.json
│   └── ...
├── lcia_categories/          # Categoria de impacto com todos os CFs
│   └── {uuid-category}.json  # Contem o array impactFactors[]
└── lcia_methods/             # Metodo LCIA referenciando as categorias
    └── {uuid-method}.json
```

Cada arquivo segue o formato JSON-LD do OpenLCA (schema v2). Os UUIDs garantem encadeamento correto entre entidades.

---

## Estrutura do Codigo-Fonte

```
src/olca_cf_converter/
├── __init__.py       # Versao do pacote
├── cli.py            # Interface de linha de comando (argparse)
├── converter.py      # Motor de conversao (pipeline completo)
├── schemas.py        # Modelos de dados (dataclasses -> JSON-LD)
└── validator.py      # Validacao de Excel e config YAML
```

Para documentacao tecnica detalhada de cada modulo, consulte [`docs/technical-reference.md`](docs/technical-reference.md).

---

## Desenvolvimento

```bash
# Instalar com dependencias de desenvolvimento
pip install -e ".[dev]"

# Rodar testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=olca_cf_converter --cov-report=term-missing
```

23 testes automatizados cobrindo schemas, validacao, conversao e CLI.

---

## Caso de Uso Original: RAICV-Brazil

O caso de uso que originou este projeto utiliza os fatores de caracterizacao da tese de doutorado da **Dra. Gabriela Giusti** (UFSCar, 2025):

> GIUSTI, Gabriela. *Development of characterization factors for health effects of particulate matter in Brazil.* 2025. Tese (Doutorado em Planejamento e Uso de Recursos Renovaveis). Universidade Federal de Sao Carlos, Sorocaba, 2025. Disponivel em: https://repositorio.ufscar.br/handle/20.500.14289/22123

Dados do caso original:
- **145 substancias** x 5 compartimentos x 28 localizacoes (Brasil + 27 estados)
- **725 fatores** de caracterizacao em DALY/kg
- Categoria: formacao de material particulado (PMFP) — endpoint
- Compativel com Ecoinvent via reuso de IDs

A configuracao esta em `configs/raicv-brazil-pmfp.yaml`.

---

## Projeto de Pos-Doutorado

Este repositorio integra o projeto de Pos-Doutorado da **Dra. Yara de Souza Tadano**, com foco em Analise de Ciclo de Vida (ACV) e no desenvolvimento de ferramentas computacionais abertas para facilitar a criacao, distribuicao e integracao de metodos LCIA regionalizados no OpenLCA.

O objetivo e reduzir a barreira tecnica entre o desenvolvimento de novos fatores de caracterizacao pela comunidade cientifica e a sua efetiva utilizacao por praticantes de ACV, promovendo reprodutibilidade e transparencia na avaliacao de impacto ambiental.

---

## Licenca

MIT License — veja [LICENSE](LICENSE).

---

## Autora

**Dra. Yara de Souza Tadano** — Pesquisadora, Pos-Doutorado em Analise de Ciclo de Vida
