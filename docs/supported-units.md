# Unidades Suportadas

O `olca-cf-converter` suporta **qualquer unidade** — basta configurar no YAML. Abaixo, as unidades mais comuns em LCIA.

## Unidades de Entrada (emissão/recurso)

| Unidade | Property Name | Uso |
|---------|--------------|-----|
| `kg` | Mass | Emissões ao ar, água, solo |
| `m³` | Volume | Uso de água |
| `m²·yr` | Area*time | Uso do solo |
| `MJ` | Energy | Recursos energéticos |
| `kBq` | Radioactivity | Emissões radioativas |

## Unidades de Saída (impacto)

### Midpoint

| Unidade | Property Name | Categoria |
|---------|--------------|-----------|
| `kg CO2-Eq` | Global warming potential | Mudança climática |
| `mol H+-Eq` | Acidification potential | Acidificação |
| `kg P-Eq` | Eutrophication potential | Eutrofização (água doce) |
| `kg N-Eq` | Marine eutrophication potential | Eutrofização (marinha) |
| `kg CFC-11-Eq` | Ozone depletion potential | Depleção da camada de ozônio |
| `kg NMVOC-Eq` | Photochemical ozone formation | Formação de ozônio fotoquímico |
| `CTUh` | Comparative toxic unit for humans | Toxicidade humana |
| `CTUe` | Comparative toxic unit for ecosystems | Ecotoxicidade |
| `kg Cu-Eq` | Mineral resource depletion | Depleção de recursos minerais |
| `kg Sb-Eq` | Abiotic depletion potential | Depleção abiótica |
| `kBq Co-60-Eq` | Ionizing radiation potential | Radiação ionizante |
| `disease incidence` | Particulate matter formation | Formação de PM (midpoint) |

### Endpoint

| Unidade | Property Name | Categoria |
|---------|--------------|-----------|
| `DALY` | Impact on human health | Saúde humana |
| `PDF·m²·yr` | Potentially disappeared fraction | Qualidade dos ecossistemas |
| `species·yr` | Species loss | Perda de espécies |
| `USD` | Financial cost | Recursos / Dano econômico |
