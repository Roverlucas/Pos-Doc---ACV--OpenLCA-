# olca-cf-converter

**Converta planilhas de Fatores de Caracterização em pacotes JSON-LD importáveis no OpenLCA.**

Ferramenta open-source para pesquisadores de Análise de Ciclo de Vida (ACV) que desenvolvem métodos LCIA regionalizados ou adaptados. Automatiza a conversão de uma planilha Excel com fatores de caracterização (CFs) em um pacote ZIP pronto para importar no [OpenLCA](https://www.openlca.org/).

---

## Por que usar?

Pesquisadores que desenvolvem novos fatores de caracterização (em teses, dissertações ou artigos) frequentemente enfrentam o trabalho manual de converter centenas de fatores em arquivos JSON-LD compatíveis com o OpenLCA. Este processo é:

- **Tedioso** — cada flow, unidade e fator precisa de um arquivo JSON separado
- **Propenso a erros** — IDs devem ser consistentes entre arquivos e compatíveis com bancos de dados existentes (Ecoinvent)
- **Não documentado** — o formato JSON-LD do OpenLCA tem nuances não cobertas na documentação oficial

O `olca-cf-converter` resolve isso com **uma linha de comando**.

---

## Funcionalidades

- **Qualquer categoria de impacto** — DALY, kg CO2-eq, mol H+-eq, CTUe, PDF·m²·yr, etc.
- **Qualquer tipo** — endpoint ou midpoint
- **Reuso de IDs Ecoinvent** — mantém compatibilidade com bancos de dados existentes
- **Regionalização** — suporta fatores por localização (país, estado, região)
- **Validação de entrada** — verifica o Excel antes de converter
- **Configuração via YAML** — sem editar código Python
- **CLI simples** — `olca-cf convert config.yaml`

---

## Início Rápido

### 1. Instalar

```bash
# Clonar o repositório
git clone https://github.com/Roverlucas/pos-doc-acv-openlca.git
cd pos-doc-acv-openlca

# Criar ambiente virtual e instalar
python3 -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

pip install -e ".[dev]"
```

### 2. Preparar sua planilha Excel

Crie um arquivo `.xlsx` com estas colunas:

| Flow | Category | Factor | Unit | Location |
|------|----------|--------|------|----------|
| Ammonia | Elementary flows/Emission to air/unspecified | 0.000579 | DALY | Brazil |
| Ammonia | Elementary flows/Emission to air/high population density | 0.000579 | DALY | Brazil, São Paulo |
| Nitrogen oxides | Elementary flows/Emission to air/unspecified | 0.001230 | DALY | Brazil |

**Dicas:**
- `Flow`: nome da substância (deve coincidir com o Ecoinvent para reuso de IDs)
- `Category`: caminho completo do compartimento ambiental no OpenLCA
- `Factor`: valor numérico do fator de caracterização
- `Unit`: unidade de saída (informativo — a unidade real vem do config)
- `Location`: localização geográfica (para fatores regionalizados)

### 3. Criar config YAML

```bash
olca-cf init -o meu-metodo.yaml
```

Edite o arquivo gerado:

```yaml
method:
  name: "Meu Método LCIA"
  description: "Descrição com referência bibliográfica."

category:
  name: "minha categoria de impacto"
  description: "Fatores de caracterização para..."
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
```

### 4. Converter

```bash
olca-cf convert meu-metodo.yaml
```

Saída:
```
============================================================
  olca-cf-converter v1.0.0
============================================================

  Method:   Meu Método LCIA
  Category: minha categoria de impacto
  Units:    kg → DALY
  Excel:    meus-fatores.xlsx

  Converting...

  ✓ Loaded 725 characterization factors from Excel
  ✓ Loaded 1842 reference flow IDs
  ✓ Flows: 680 reused IDs + 45 new = 725 total
  ✓ Impact category: 725 factors
  ✓ Method: Meu Método LCIA
  ✓ Output: Meu-Metodo-FINAL.zip (734 files)

  ✅ Done! Import this file into OpenLCA:
     Meu-Metodo-FINAL.zip

  OpenLCA: File → Import → JSON-LD → select the ZIP
```

### 5. Importar no OpenLCA

1. Abra o OpenLCA
2. Vá em **File → Import**
3. Selecione **JSON-LD Zip**
4. Navegue até o arquivo `.zip` gerado
5. Clique em **Finish**

O método aparecerá em **Impact assessment methods** no navegador do OpenLCA.

---

## Exemplos de Configuração

### Mudança Climática (GWP - midpoint)

```yaml
method:
  name: "GWP Regionalizado Brasil"
  description: "Potenciais de aquecimento global adaptados."
category:
  name: "climate change - GWP100"
  type: midpoint
units:
  input: { name: kg, property: Mass }
  output: { name: "kg CO2-Eq", property: "Global warming potential" }
```

### Acidificação (midpoint)

```yaml
method:
  name: "Acidificação Regional"
  description: "Potenciais de acidificação regionalizados."
category:
  name: "terrestrial acidification - TAP"
  type: midpoint
units:
  input: { name: kg, property: Mass }
  output: { name: "mol H+-Eq", property: "Acidification potential" }
```

### Ecotoxicidade (midpoint)

```yaml
method:
  name: "Ecotoxicidade Aquática"
  description: "Fatores de ecotoxicidade para água doce."
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
  input: { name: "m²·yr", property: "Area*time" }
  output: { name: "PDF·m²·yr", property: "Potentially disappeared fraction" }
```

---

## Validar Excel antes de converter

```bash
olca-cf validate meus-fatores.xlsx
```

Verifica:
- Colunas obrigatórias presentes
- Valores numéricos na coluna Factor
- Nomes de flows não vazios
- Formato do arquivo (.xlsx)

---

## Estrutura do pacote gerado

```
Meu-Metodo-FINAL.zip
├── openlca.json              # Manifesto (schemaVersion: 2)
├── units/                    # Definições de unidades (kg, DALY, etc.)
├── unit_groups/              # Grupos de unidades
├── flow_properties/          # Propriedades de fluxo (Mass, Impact, etc.)
├── flows/                    # Fluxos elementares (substâncias)
├── lcia_categories/          # Categoria de impacto com todos os CFs
└── lcia_methods/             # Método LCIA referenciando as categorias
```

---

## Reuso de IDs Ecoinvent

Quando você fornece um `reference_zip` (exportação do Ecoinvent ou outro banco de dados), a ferramenta:

1. Lê todos os flows do ZIP de referência
2. Para cada (nome, categoria) na sua planilha, verifica se já existe no Ecoinvent
3. Se existir, **reutiliza o UUID** — garantindo que seu método se conecte aos processos existentes
4. Se não existir, gera um novo UUID

Isso é fundamental para que os fatores de caracterização funcionem com inventários existentes no OpenLCA.

---

## Desenvolvimento

```bash
# Rodar testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=olca_cf_converter --cov-report=term-missing
```

---

## Categorias de impacto suportadas

A ferramenta é **genérica** — funciona com qualquer combinação de unidade de entrada/saída. Exemplos comuns:

| Categoria | Tipo | Unidade de Saída |
|-----------|------|------------------|
| Mudança climática (GWP) | midpoint | kg CO2-Eq |
| Acidificação terrestre | midpoint | mol H+-Eq |
| Eutrofização aquática | midpoint | kg P-Eq |
| Formação de material particulado | endpoint | DALY |
| Toxicidade humana (câncer) | midpoint | CTUh |
| Ecotoxicidade aquática | midpoint | CTUe |
| Depleção de ozônio | midpoint | kg CFC-11-Eq |
| Uso do solo | endpoint | PDF·m²·yr |
| Depleção de recursos minerais | midpoint | kg Cu-Eq |
| Radiação ionizante | midpoint | kBq Co-60-Eq |

---

## Caso de uso original: RAICV-Brazil

Este projeto foi criado a partir do trabalho da **Dra. Gabriela Giusti** (UFSCar, 2025), que desenvolveu fatores de caracterização regionalizados para material particulado no Brasil:

> GIUSTI, Gabriela. *Development of characterization factors for health effects of particulate matter in Brazil.* 2025. Tese (Doutorado em Planejamento e Uso de Recursos Renováveis). Universidade Federal de São Carlos, Sorocaba, 2025.

- **145 substâncias** × 5 compartimentos × 28 localizações (Brasil + 27 estados)
- **725 fatores** de caracterização em DALY/kg
- Compatível com Ecoinvent via reuso de IDs

A configuração original está em `configs/raicv-brazil-pmfp.yaml`.

---

## Licença

MIT License — veja [LICENSE](LICENSE).

---

## Autor

**Lucas Rover**
UTFPR — Programa de Pós-Graduação em Sustentabilidade Ambiental Urbana
[ORCID: 0000-0001-6641-9224](https://orcid.org/0000-0001-6641-9224)
