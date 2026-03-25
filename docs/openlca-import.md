# Importar no OpenLCA

## Passo a passo

### 1. Abrir o OpenLCA

Certifique-se de que você tem um banco de dados ativo (com ou sem Ecoinvent importado).

### 2. Importar o ZIP

1. Vá em **File → Import**
2. Na janela de importação, selecione **Linked Data (JSON-LD)**
3. Clique em **Next**
4. Em **File**, navegue até o arquivo `.zip` gerado pelo `olca-cf-converter`
5. Clique em **Finish**

### 3. Verificar a importação

Após a importação, verifique:

1. **Impact assessment methods** → Seu método deve aparecer na lista
2. Clique no método → verifique as **Impact categories**
3. Clique na categoria → verifique os **Characterization factors**
4. Cada fator deve mostrar o flow, valor e unidade corretos

### 4. Testar com um produto

1. Abra um **Product system** existente
2. Vá em **Impact analysis**
3. Selecione seu método LCIA importado
4. Execute o cálculo
5. Verifique se os resultados fazem sentido

## Resolução de problemas

### Fatores não aparecem nos resultados

**Causa provável:** Os UUIDs dos flows não coincidem com os do inventário.

**Solução:**
- Use o `reference_zip` do Ecoinvent ao converter
- Ou use o **Flow mapping** do OpenLCA para conectar manualmente

### Método importado mas sem categorias

**Causa provável:** Arquivo ZIP corrompido ou estrutura incorreta.

**Solução:**
- Verifique se o ZIP contém `openlca.json` na raiz
- Rode `olca-cf validate` no seu Excel antes de converter
- Tente reimportar

### Unidades não reconhecidas

**Causa provável:** Nome da unidade diferente do esperado pelo OpenLCA.

**Solução:**
- Use nomes exatos das unidades do OpenLCA (ex: "kg", não "kilogram")
- Consulte `docs/supported-units.md` para nomes corretos
