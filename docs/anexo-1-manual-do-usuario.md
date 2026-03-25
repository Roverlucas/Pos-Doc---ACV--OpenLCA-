# ANEXO 1 — MANUAL DO USUARIO

## olca-cf-converter: Guia Passo a Passo para Iniciantes

---

### O que e esta ferramenta? (Explicacao simples)

Imagine que voce tem uma **tabela no Excel** com numeros que representam o quanto cada poluente faz mal ao meio ambiente ou a saude das pessoas. Esses numeros se chamam **fatores de caracterizacao**.

Agora imagine que existe um **programa de computador** chamado OpenLCA que os profissionais de meio ambiente usam para calcular os impactos de produtos (como uma garrafa, um carro, uma construcao). So que esse programa nao consegue ler sua tabela do Excel diretamente. Ele precisa receber os dados em um formato especial — um "pacote" com muitos arquivos organizados de um jeito bem especifico.

**Esta ferramenta faz essa traducao para voce.** Ela pega sua tabela do Excel, organiza tudo no formato que o OpenLCA entende, e entrega um arquivo pronto para ser importado. Voce nao precisa saber programar.

```
Sua tabela (Excel)  -->  [olca-cf-converter]  -->  Pacote pronto (ZIP)  -->  OpenLCA
```

---

### Glossario: Termos tecnicos traduzidos

Antes de comecar, aqui vai um dicionario dos termos que voce vai encontrar. Nao precisa decorar — consulte quando precisar.

| Termo tecnico | O que significa (linguagem simples) |
|---------------|-------------------------------------|
| **Fator de caracterizacao (CF)** | Um numero que diz "quanto de impacto ambiental 1 kg de certo poluente causa". Por exemplo: 1 kg de amonia causa 0,000579 anos de vida perdidos (DALY). |
| **LCIA** | Sigla em ingles para "Avaliacao de Impacto do Ciclo de Vida". E a etapa em que os numeros do inventario sao convertidos em impactos ambientais. |
| **OpenLCA** | Um programa gratuito de computador que profissionais usam para fazer Avaliacao de Ciclo de Vida. Funciona como o "Excel da ACV". |
| **JSON-LD** | O "idioma" que o OpenLCA fala. E um formato de arquivo de texto com uma estrutura rigida. Voce nao precisa mexer nele — a ferramenta cria automaticamente. |
| **UUID** | Um codigo unico (como um CPF, so que para substancias quimicas). Exemplo: `9990b51b-7023-4700-bca0-1a32ef921f74`. O OpenLCA usa esses codigos para conectar as coisas entre si. |
| **Ecoinvent** | O maior banco de dados de inventario ambiental do mundo. Contem informacoes sobre milhares de processos industriais. |
| **ZIP** | Um arquivo compactado (como um .rar). Dentro dele ficam muitos outros arquivos organizados em pastas. |
| **YAML** | Um arquivo de texto simples onde voce escreve configuracoes. E como preencher um formulario em texto. |
| **CLI** | Interface de Linha de Comando — significa que voce digita comandos no computador em vez de clicar em botoes. Parece complicado, mas sao apenas 3 comandos. |
| **Terminal** | A tela preta (ou branca) onde voce digita comandos. No Mac chama "Terminal", no Windows chama "Prompt de Comando" ou "PowerShell". |
| **Python** | A linguagem de programacao em que a ferramenta foi escrita. Voce precisa ter instalado, mas nao precisa saber programar em Python. |
| **Flow** | Uma substancia que e emitida ao meio ambiente (ex: amonia, dioxido de enxofre, oxidos de nitrogenio). |
| **Endpoint** | Dano final (ex: anos de vida perdidos — DALY). |
| **Midpoint** | Impacto intermediario (ex: kg de CO2 equivalente para aquecimento global). |
| **DALY** | Disability-Adjusted Life Years — "anos de vida saudavel perdidos". E a unidade que mede o dano a saude humana. |

---

### O que voce precisa ter no computador

Antes de comecar, verifique se tem estas duas coisas:

**1. Python (versao 3.10 ou mais recente)**

Para verificar, abra o Terminal e digite:

```
python3 --version
```

Se aparecer algo como `Python 3.10.x` ou superior, esta tudo certo. Se nao aparecer nada ou der erro, voce precisa instalar o Python:
- **Mac:** Abra o Terminal e digite `brew install python` (precisa do Homebrew) ou baixe em https://www.python.org/downloads/
- **Windows:** Baixe o instalador em https://www.python.org/downloads/ e **marque a opcao "Add Python to PATH"** durante a instalacao

**2. Acesso ao Terminal**

- **Mac:** Abra o aplicativo "Terminal" (esta na pasta Utilitarios)
- **Windows:** Procure "PowerShell" no menu Iniciar

Pronto. So isso.

---

### Passo 1: Baixar a ferramenta

Abra o Terminal e copie/cole estes comandos **um de cada vez**, apertando Enter apos cada um:

```
git clone https://github.com/Roverlucas/Pos-Doc---ACV--OpenLCA-.git
```

> **O que esse comando faz:** Baixa todos os arquivos da ferramenta do GitHub (uma plataforma onde programas sao compartilhados) para o seu computador.

```
cd Pos-Doc---ACV--OpenLCA-
```

> **O que esse comando faz:** Entra na pasta que acabou de ser baixada. E como dar um duplo clique numa pasta.

---

### Passo 2: Preparar o ambiente

```
python3 -m venv .venv
```

> **O que esse comando faz:** Cria uma "caixa de areia" no seu computador onde a ferramenta vai funcionar, sem interferir em nada mais que voce tenha instalado. Isso se chama "ambiente virtual".

Agora, ative essa caixa de areia:

- **Mac/Linux:**
  ```
  source .venv/bin/activate
  ```

- **Windows:**
  ```
  .venv\Scripts\activate
  ```

> **Como saber se funcionou:** Vai aparecer `(.venv)` no comeco da linha do Terminal. Isso significa que a caixa de areia esta ativa.

Agora instale a ferramenta:

```
pip install -e ".[dev]"
```

> **O que esse comando faz:** Instala a ferramenta e tudo que ela precisa para funcionar (como instalar um aplicativo). Pode demorar 1-2 minutos.

**Pronto!** A ferramenta esta instalada. Voce so precisa fazer os Passos 1 e 2 UMA VEZ. Nas proximas vezes, basta ativar a caixa de areia (o comando `source .venv/bin/activate`) e ja pode usar.

---

### Passo 3: Preparar sua planilha Excel

Abra o Excel (ou Google Sheets, ou LibreOffice Calc) e crie uma tabela com exatamente estas 5 colunas:

| Flow | Category | Factor | Unit | Location |
|------|----------|--------|------|----------|
| Ammonia | Elementary flows/Emission to air/unspecified | 0.000579 | DALY | Brazil |
| Nitrogen oxides | Elementary flows/Emission to air/high population density | 0.001230 | DALY | Brazil, Sao Paulo |

**Explicacao de cada coluna:**

- **Flow** = Nome da substancia (poluente) em ingles. Use o MESMO nome que aparece no Ecoinvent. Exemplos: "Ammonia", "Sulfur dioxide", "Nitrogen oxides", "Particulate Matter, < 2.5 um".

- **Category** = O "endereco" de onde essa substancia e emitida. E sempre um caminho que comeca com "Elementary flows/" seguido do tipo de emissao. Os mais comuns sao:
  - `Elementary flows/Emission to air/unspecified` (emissao ao ar, sem especificar)
  - `Elementary flows/Emission to air/high population density` (emissao ao ar em area com muita gente)
  - `Elementary flows/Emission to air/low population density` (emissao ao ar em area com pouca gente)
  - `Elementary flows/Emission to water/unspecified` (emissao a agua)
  - `Elementary flows/Emission to soil/unspecified` (emissao ao solo)

- **Factor** = O numero do fator de caracterizacao. Deve ser um numero (com ponto decimal, nao virgula). Exemplo: `0.000579` (e nao `0,000579`).

- **Unit** = A unidade do impacto. Exemplos: "DALY", "kg CO2-Eq", "mol H+-Eq". Essa coluna e informativa — a unidade real e definida no arquivo de configuracao.

- **Location** = O lugar para o qual o fator vale. Exemplos: "Brazil", "Brazil, Sao Paulo", "Brazil, Minas Gerais", "Global". Se os seus fatores nao sao regionalizados, coloque "Global" em todas as linhas.

**Salve o arquivo como `.xlsx`** (formato Excel padrao). Exemplo: `meus-fatores.xlsx`.

**Dica importante:** Nao deixe celulas vazias na coluna Flow. Nao misture texto com numeros na coluna Factor. Se houver esses problemas, a ferramenta vai avisar.

---

### Passo 4: Criar o arquivo de configuracao

O arquivo de configuracao e como um "formulario" que diz para a ferramenta: qual e o nome do seu metodo, qual e a unidade, onde esta a planilha, etc.

Para gerar um modelo em branco, digite no Terminal:

```
olca-cf init -o meu-metodo.yaml
```

> **O que esse comando faz:** Cria um arquivo chamado `meu-metodo.yaml` com todos os campos para voce preencher.

Agora abra o arquivo `meu-metodo.yaml` em qualquer editor de texto (Bloco de Notas, TextEdit, VS Code, Notepad++) e preencha:

```yaml
# CONFIGURACAO DO MEU METODO
# Linhas que comecam com # sao comentarios (o computador ignora)

method:
  name: "RAICV-Brazil - PMFP"
  description: "Fatores de caracterizacao para formacao de material particulado, regionalizados para os estados brasileiros (Giusti, 2025)."

category:
  name: "particulate matter formation - PMFP"
  description: "Fatores em DALY/kg para material particulado."
  type: endpoint
  #
  # DICA: Use "endpoint" se a unidade e DALY, PDF*m2*yr, species*yr
  #       Use "midpoint" se a unidade e kg CO2-Eq, mol H+-Eq, CTUe, etc.

units:
  input:
    name: kg
    property: Mass
    #
    # DICA: Quase sempre sera "kg" e "Mass".
    #       So mude se sua entrada nao for massa (ex: m2*yr para uso do solo).
  output:
    name: DALY
    property: "Impact on human health"
    #
    # DICA: Mude conforme a unidade do seu fator:
    #   DALY               -> "Impact on human health"
    #   kg CO2-Eq          -> "Global warming potential"
    #   mol H+-Eq          -> "Acidification potential"
    #   CTUe               -> "Comparative toxic unit for ecosystems"
    #   CTUh               -> "Comparative toxic unit for humans"

files:
  excel: "meus-fatores.xlsx"
  #
  # DICA: Coloque o caminho para a sua planilha.
  #       Se a planilha esta na mesma pasta do config, basta o nome.

  reference_zip: "Base-Ecoinvent.zip"
  #
  # DICA: Se voce tem uma exportacao do Ecoinvent, coloque aqui.
  #       Se nao tem, apague esta linha ou escreva: reference_zip: null
  #       Sem isso, os fatores vao funcionar, mas nao se conectam
  #       automaticamente aos processos do Ecoinvent no OpenLCA.

  model_zip: null
  #
  # DICA: Pode deixar como null (sem modelo base).

  output_zip: "Meu-Metodo-FINAL.zip"
  #
  # DICA: Escolha o nome do arquivo final que sera gerado.
```

**Salve o arquivo.** Pronto — a configuracao esta feita.

---

### Passo 5: Verificar a planilha (opcional, mas recomendado)

Antes de converter, e uma boa ideia verificar se a planilha esta correta:

```
olca-cf validate meus-fatores.xlsx
```

Se tudo estiver certo, voce vera:

```
  Validating: meus-fatores.xlsx

  Rows:        725
  Flows:       145 unique substances
  Categories:  5 compartments
  Locations:   28 regions
  Unit:        DALY
  Factor range: 0.000000e+00 to 5.119727e-03

  Excel file is valid!
```

Se houver algum problema, a ferramenta dira exatamente o que esta errado. Por exemplo:

- "Missing required columns: ['Location']" = Falta a coluna Location na planilha
- "Non-numeric values in 'Factor' column" = Ha texto onde deveria ter numero na coluna Factor
- "Empty flow names at rows: [5, 12]" = As linhas 5 e 12 tem o nome do flow vazio

---

### Passo 6: Converter!

Este e o momento principal. Digite:

```
olca-cf convert meu-metodo.yaml
```

Voce vera uma saida como esta:

```
============================================================
  olca-cf-converter v1.0.0
============================================================

  Method:   RAICV-Brazil - PMFP
  Category: particulate matter formation - PMFP
  Units:    kg -> DALY
  Excel:    meus-fatores.xlsx

  Converting...

  ✓ Base structure loaded from model
  ✓ Loaded 8902 reference flow IDs
  ✓ Loaded 725 characterization factors from Excel
  ✓ Flows: 20 reused IDs + 705 new = 725 total
  ✓ Impact category: 725 factors
  ✓ Method: RAICV-Brazil - PMFP
  ✓ Output: Meu-Metodo-FINAL.zip (734 files)

  Done! Import this file into OpenLCA:
     Meu-Metodo-FINAL.zip

  OpenLCA: File -> Import -> JSON-LD -> select the ZIP
```

**Pronto!** O arquivo `Meu-Metodo-FINAL.zip` foi criado. Este e o pacote que voce vai importar no OpenLCA.

---

### Passo 7: Importar no OpenLCA

1. Abra o **OpenLCA** no seu computador
2. Certifique-se de que tem um **banco de dados ativo** (aparece no lado esquerdo)
3. Clique no menu **File** (Arquivo)
4. Clique em **Import** (Importar)
5. Na janela que abrir, selecione **Linked Data (JSON-LD)**
6. Clique em **Next** (Proximo)
7. Clique em **Browse** (Procurar) e navegue ate o arquivo `Meu-Metodo-FINAL.zip`
8. Clique em **Finish** (Concluir)
9. Aguarde a importacao (pode levar alguns segundos)

**Onde encontrar o metodo importado:**
- No navegador do OpenLCA (lado esquerdo), expanda **Impact assessment methods**
- Voce vera seu metodo (ex: "RAICV-Brazil - PMFP")
- Clique nele para ver as categorias e fatores

---

### Resumo rapido (cola)

```
# Primeira vez (instalacao):
git clone https://github.com/Roverlucas/Pos-Doc---ACV--OpenLCA-.git
cd Pos-Doc---ACV--OpenLCA-
python3 -m venv .venv
source .venv/bin/activate        # Mac/Linux
pip install -e ".[dev]"

# Uso (toda vez):
source .venv/bin/activate        # Ativar ambiente
olca-cf validate meu-excel.xlsx  # Verificar planilha
olca-cf convert meu-config.yaml  # Converter para OpenLCA
# -> Importar o ZIP no OpenLCA: File -> Import -> JSON-LD
```

---

### Perguntas frequentes

**"Preciso saber programar?"**
Nao. Voce so precisa preparar a planilha no Excel e preencher o arquivo de configuracao (que e um texto simples). Os comandos no Terminal sao copiados e colados.

**"Funciona no Windows?"**
Sim. Funciona em Windows, Mac e Linux. Basta ter Python 3.10+ instalado.

**"E se eu nao tenho a base do Ecoinvent?"**
A ferramenta funciona sem ela. Basta colocar `reference_zip: null` no config. A unica diferenca e que os fatores nao se conectam automaticamente aos processos do Ecoinvent no OpenLCA — voce precisaria fazer isso manualmente depois (pelo Flow Mapping).

**"Posso usar para qualquer tipo de impacto?"**
Sim. A ferramenta e generica. Funciona para material particulado (DALY), mudanca climatica (kg CO2-Eq), acidificacao (mol H+-Eq), ecotoxicidade (CTUe), toxicidade humana (CTUh), uso do solo (PDF*m2*yr) e qualquer outra categoria de impacto.

**"Meus fatores nao sao regionalizados. Posso usar?"**
Sim. Coloque "Global" na coluna Location para todas as linhas.

**"Algo deu errado. O que faco?"**
1. Rode `olca-cf validate` na sua planilha — ele indica o problema exato
2. Verifique se os nomes das colunas no Excel coincidem com o que esta no config YAML
3. Verifique se salvou o Excel como `.xlsx` (nao como `.csv`)
4. Verifique se o ambiente virtual esta ativado (deve aparecer `(.venv)` no Terminal)

**"Posso usar o Google Sheets?"**
Sim, desde que exporte como `.xlsx` (Arquivo -> Baixar -> Microsoft Excel).
