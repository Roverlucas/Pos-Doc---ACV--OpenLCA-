# Reuso de IDs Ecoinvent

## Por que reaproveitar IDs?

No OpenLCA, cada fluxo elementar (substância) é identificado por um UUID único. Quando você importa um método LCIA, o OpenLCA conecta os fatores de caracterização aos processos do inventário **por UUID**.

Se você criar UUIDs novos para substâncias que já existem no Ecoinvent, os fatores **não serão aplicados** aos processos do inventário — mesmo que o nome seja idêntico.

## Como funciona

```
Sua planilha Excel          Base Ecoinvent (reference_zip)
┌──────────────────┐       ┌──────────────────────────────┐
│ Flow: "Ammonia"  │       │ Flow: "Ammonia"              │
│ Cat: ".../air/…" │──────>│ Cat: ".../air/…"             │
│                  │ match │ @id: "9990b51b-7023-..."     │
└──────────────────┘       └──────────────────────────────┘
         │                              │
         │         reusa o UUID         │
         ▼                              │
┌──────────────────┐                    │
│ Flow gerado:     │<───────────────────┘
│ @id: "9990b51b…" │  ← mesmo ID = compatível
└──────────────────┘
```

## Matching por (nome, categoria)

A ferramenta faz o match usando a **combinação exata** de:
- **nome do flow** (ex: "Ammonia")
- **categoria completa** (ex: "Elementary flows/Emission to air/high population density")

Se ambos coincidirem, o UUID é reaproveitado. Caso contrário, um novo UUID é gerado.

## Como obter o reference_zip

### Opção 1: Exportar do OpenLCA
1. Abra o OpenLCA com o banco de dados Ecoinvent importado
2. Clique com botão direito no banco → **Export**
3. Selecione **JSON-LD Zip**
4. Use o ZIP gerado como `reference_zip`

### Opção 2: Exportar apenas os flows
1. Na árvore do OpenLCA, expanda **Elementary flows**
2. Selecione todos → **Export**
3. Isso gera um ZIP menor, contendo apenas os flows

## Sem reference_zip

Se você não fornecer um `reference_zip`, a ferramenta gera UUIDs novos para todos os flows. O método funcionará no OpenLCA, mas **não se conectará automaticamente** a processos de bancos de dados existentes.

Neste caso, você precisará fazer o matching manualmente no OpenLCA (Flow mapping).
