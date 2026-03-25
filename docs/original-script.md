# Script Original — Referencia Historica

Este documento descreve o script original (`FINAL-correto-reused-ids.py`) que serviu de base para o `olca-cf-converter`. Mantido para rastreabilidade e compreensao da evolucao do projeto.

---

## Visao Geral

O script original e um arquivo Python monolitico de 330 linhas que converte a planilha de fatores de caracterizacao da Dra. Gabriela Giusti (RAICV-Brazil, PMFP) em um pacote JSON-LD importavel no OpenLCA.

## Entradas

| Arquivo | Descricao |
|---------|-----------|
| `CF-DALY-Giusti-Flows.xlsx` | Planilha com 725 CFs (Flow, Category, Factor, Unit, Location) |
| `RAICV-Brazil-modelo.zip` | Estrutura base do OpenLCA (pastas vazias, openlca.json) |
| `Base-Ecoinvent.zip` | Exportacao de flows do Ecoinvent para reuso de UUIDs |

## Saida

| Arquivo | Descricao |
|---------|-----------|
| `RAICV-Brazil-FINAL.zip` | Pacote completo para importacao no OpenLCA |

## Fluxo de Execucao

```
1. Preparar pastas temporarias
2. Extrair RAICV-Brazil-modelo.zip (estrutura base)
3. Extrair Base-Ecoinvent.zip (flows de referencia)
4. Ler planilha Excel com pandas
5. Gerar UUIDs para unidades (kg, DALY), grupos e propriedades
6. Escrever JSONs de unidades, grupos e propriedades
7. Ler flows existentes do Ecoinvent -> dict (name, category) -> UUID
8. Para cada (Flow, Category) unico na planilha:
   - Se existe no Ecoinvent: reusar UUID
   - Se nao: gerar uuid4()
   - Escrever flows/{uuid}.json
9. Construir mapa (Flow, Category, Location) -> UUID
10. Criar ImpactCategory com array de impactFactors
11. Criar ImpactMethod referenciando a categoria
12. Compactar tudo em ZIP
13. Limpar pastas temporarias
```

## Limitacoes do Script Original

- **Hardcoded:** nomes do metodo, categoria, unidades e descricao diretamente no codigo
- **Sem validacao:** nao verifica se o Excel tem as colunas corretas
- **Sem CLI:** para alterar parametros, e necessario editar o .py
- **Sem testes:** nenhum teste automatizado
- **Unico caso:** funciona apenas para PMFP/DALY, nao e generico
- **Codigo comentado:** versoes alternativas (Oberschelp) estao como comentarios no codigo
- **Bug de concatenacao:** a descricao do metodo usa concatenacao implicita de strings Python (linhas 298-302), o que funciona mas e fragil

## Evolucao

O `olca-cf-converter` generaliza toda a logica do script original, parametrizando via YAML o que antes era hardcoded. A logica de conversao (formato JSON-LD, deduplicacao, reuso de IDs) e preservada identica.
