"""
schemas.py — Modelos de dados para entidades do OpenLCA no formato JSON-LD.

Este modulo define TODAS as entidades que o OpenLCA espera encontrar dentro de
um pacote ZIP importavel. Cada classe aqui representa um tipo de arquivo JSON
que sera gerado.

CONCEITO-CHAVE: No OpenLCA, tudo e identificado por UUIDs (identificadores
unicos universais). Quando voce importa um pacote, o OpenLCA usa esses UUIDs
para conectar as entidades entre si. Por exemplo, um fator de caracterizacao
aponta para um flow pelo UUID — se o UUID nao bater, o fator nao e aplicado.

HIERARQUIA DAS ENTIDADES (de baixo para cima):
    UnitDef (kg, DALY)
      -> UnitGroupDef (agrupa unidades compativeis)
        -> FlowPropertyDef (propriedade: Mass, Volume, Impact)
          -> FlowDef (substancia: Ammonia, NOx, SO2)
            -> ImpactFactorDef (valor numerico do CF)
              -> ImpactCategoryDef (categoria: GWP, PMFP, TAP)
                -> ImpactMethodDef (metodo: ReCiPe, RAICV-Brazil)

Usamos dataclasses do Python para ter tipagem, validacao automatica e
facilidade de leitura. O metodo to_dict() de cada classe gera o dicionario
Python que sera salvo como JSON.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


def new_uuid() -> str:
    """Gera um UUID v4 aleatorio no formato string.

    UUIDs v4 sao aleatorios e praticamente unicos (probabilidade de colisao
    e ~1 em 2^122). O OpenLCA usa UUIDs para identificar TODAS as entidades.

    Exemplo de saida: "9990b51b-7023-4700-bca0-1a32ef921f74"
    """
    return str(uuid.uuid4())


# =============================================================================
# UNIDADE (Unit)
# =============================================================================
# Representa uma unidade de medida, como "kg", "DALY", "kg CO2-Eq".
# No OpenLCA, cada unidade e um arquivo JSON dentro da pasta units/.
# =============================================================================

@dataclass
class UnitDef:
    # Nome da unidade (ex: "kg", "DALY", "mol H+-Eq")
    name: str
    # UUID gerado automaticamente — identifica esta unidade de forma unica
    uid: str = field(default_factory=new_uuid)


# =============================================================================
# GRUPO DE UNIDADES (UnitGroup)
# =============================================================================
# Agrupa unidades que sao compativeis entre si. Por exemplo, o grupo "Mass
# units" contem kg, g, mg, ton. No nosso caso simplificado, cada grupo tem
# apenas uma unidade (a de referencia).
#
# O OpenLCA exige que toda unidade pertenca a um grupo. Sem o grupo, a
# importacao falha silenciosamente.
# =============================================================================

@dataclass
class UnitGroupDef:
    # Nome do grupo (ex: "Mass units", "Impact units")
    name: str
    # Unidade de referencia deste grupo
    unit: UnitDef
    # Categoria no OpenLCA (define onde aparece na arvore do software)
    category: str = "Technical unit groups"
    uid: str = field(default_factory=new_uuid)

    def to_dict(self) -> dict:
        """Converte para o formato JSON-LD que o OpenLCA espera.

        Gera algo como:
        {
            "@type": "UnitGroup",
            "@id": "abc-123-...",
            "name": "Mass units",
            "units": [{"name": "kg", "factor": 1.0, "isReferenceUnit": true}]
        }
        """
        return {
            "@type": "UnitGroup",
            "@id": self.uid,
            "name": self.name,
            "category": self.category,
            "default": True,
            "units": [
                {
                    "@type": "Unit",
                    "@id": self.unit.uid,
                    "name": self.unit.name,
                    # factor=1.0 porque e a unidade de referencia do grupo
                    "factor": 1.0,
                    "isReferenceUnit": True,
                }
            ],
        }


# =============================================================================
# PROPRIEDADE DE FLUXO (FlowProperty)
# =============================================================================
# Define QUAL propriedade fisica um fluxo mede. Por exemplo:
#   - "Mass" (propriedade) usa o grupo "Mass units" (que contem "kg")
#   - "Impact on human health" usa "Impact units" (que contem "DALY")
#
# Cada flow no OpenLCA TEM que ter pelo menos uma FlowProperty associada.
# Sem isso, o software nao sabe em que unidade o fluxo e medido.
# =============================================================================

@dataclass
class FlowPropertyDef:
    # Nome da propriedade (ex: "Mass", "Global warming potential")
    name: str
    # Grupo de unidades associado (ex: Mass units -> kg)
    unit_group: UnitGroupDef
    # Categoria no OpenLCA
    category: str = "Technical flow properties"
    # Tipo: PHYSICAL_QUANTITY para grandezas fisicas (massa, volume, energia)
    flow_property_type: str = "PHYSICAL_QUANTITY"
    uid: str = field(default_factory=new_uuid)

    def to_dict(self) -> dict:
        """Gera o JSON-LD da FlowProperty, referenciando o UnitGroup pelo UUID."""
        return {
            "@type": "FlowProperty",
            "@id": self.uid,
            "name": self.name,
            "category": self.category,
            "flowPropertyType": self.flow_property_type,
            # Referencia ao grupo de unidades — o OpenLCA usa o @id para conectar
            "unitGroup": {
                "@type": "UnitGroup",
                "@id": self.unit_group.uid,
                "name": self.unit_group.name,
                "category": self.unit_group.category,
            },
        }


# =============================================================================
# FLUXO ELEMENTAR (Flow)
# =============================================================================
# Representa uma substancia que e emitida ou consumida. Exemplos:
#   - "Ammonia" emitida ao ar (Elementary flows/Emission to air/unspecified)
#   - "Nitrogen oxides" emitido ao ar em area de alta densidade populacional
#
# CONCEITO IMPORTANTE: No Ecoinvent e no OpenLCA, o MESMO nome de substancia
# em compartimentos diferentes (ar, agua, solo) sao flows DISTINTOS com UUIDs
# diferentes. Porem, a MESMA substancia no MESMO compartimento em localizacoes
# diferentes (SP, RJ, MG) e o MESMO flow — a regionalizacao acontece no nivel
# do fator de caracterizacao, nao do flow.
#
# flowType = "ELEMENTARY_FLOW" significa que e uma substancia que cruza a
# fronteira entre o sistema tecnico e o meio ambiente (emissao ou recurso).
# =============================================================================

@dataclass
class FlowDef:
    # Nome da substancia (ex: "Ammonia", "Sulfur dioxide")
    name: str
    # Compartimento ambiental completo (ex: "Elementary flows/Emission to air/unspecified")
    category: str
    # Propriedade de fluxo (tipicamente "Mass" com unidade "kg")
    flow_property: FlowPropertyDef
    # UUID — pode ser reaproveitado do Ecoinvent para manter compatibilidade
    uid: str = field(default_factory=new_uuid)

    def to_dict(self) -> dict:
        """Gera o JSON-LD do flow com sua propriedade de fluxo associada.

        O campo flowProperties[] e um array porque um flow pode ter multiplas
        propriedades (ex: massa E volume). No nosso caso, usamos apenas uma
        (a propriedade de referencia).
        """
        return {
            "@type": "Flow",
            "@id": self.uid,
            "name": self.name,
            "description": None,
            "category": self.category,
            "version": "00.00.000",
            # ELEMENTARY_FLOW = substancia que cruza a fronteira tecnosfera/ecosfera
            "flowType": "ELEMENTARY_FLOW",
            "casNumber": None,
            "synonyms": [],
            "isInfrastructureFlow": False,
            # Lista de propriedades de fluxo — aqui apenas a de referencia (Mass/kg)
            "flowProperties": [
                {
                    "@type": "FlowPropertyFactor",
                    # isRefFlowProperty=True indica que esta e a propriedade principal
                    "isRefFlowProperty": True,
                    "conversionFactor": 1.0,
                    "flowProperty": {
                        "@type": "FlowProperty",
                        "@id": self.flow_property.uid,
                        "name": self.flow_property.name,
                        "refUnit": self.flow_property.unit_group.unit.name,
                        "category": self.flow_property.category,
                    },
                }
            ],
            "conversionFactor": 1.0,
            "location": None,
        }


# =============================================================================
# FATOR DE CARACTERIZACAO (ImpactFactor)
# =============================================================================
# E o valor numerico que converte uma emissao em impacto ambiental.
# Exemplo: emitir 1 kg de Ammonia ao ar causa 0.000579 DALY de dano a saude.
#
# Cada fator conecta:
#   - Um FLOW (qual substancia)
#   - Um VALOR numerico (quanto impacto por unidade de emissao)
#   - Uma UNIDADE de entrada (em que unidade a emissao e medida)
#   - Uma PROPRIEDADE de fluxo (qual grandeza fisica)
#
# No JSON gerado, cada fator referencia o flow, a unidade e a propriedade
# pelos seus UUIDs — e assim que o OpenLCA sabe "para qual substancia do
# inventario este fator se aplica".
# =============================================================================

@dataclass
class ImpactFactorDef:
    # Valor do fator de caracterizacao (ex: 0.000579 DALY/kg para Ammonia)
    value: float
    # Flow ao qual este fator se aplica
    flow: FlowDef
    # Unidade de entrada (tipicamente kg)
    input_unit: UnitDef
    # Propriedade de fluxo de entrada (tipicamente Mass)
    input_flow_property: FlowPropertyDef

    def to_dict(self) -> dict:
        """Gera o JSON-LD do fator de caracterizacao.

        Este e o formato que aparece dentro do array impactFactors[] da
        ImpactCategory. O OpenLCA le cada entrada deste array e conecta
        ao flow correspondente pelo @id.
        """
        return {
            # Valor numerico do CF (ex: 0.000579)
            "value": self.value,
            # Referencia ao flow — o @id DEVE existir na pasta flows/ do ZIP
            "flow": {
                "@type": "Flow",
                "@id": self.flow.uid,
                "name": self.flow.name,
                "category": self.flow.category,
                "flowType": "ELEMENTARY_FLOW",
                "refUnit": self.input_flow_property.unit_group.unit.name,
            },
            # Unidade em que a emissao e medida (ex: kg)
            "unit": {
                "@type": "Unit",
                "@id": self.input_unit.uid,
                "name": self.input_unit.name,
            },
            # Propriedade de fluxo (ex: Mass)
            "flowProperty": {
                "@type": "FlowProperty",
                "@id": self.input_flow_property.uid,
                "category": self.input_flow_property.category,
                "name": self.input_flow_property.name,
                "refUnit": self.input_flow_property.unit_group.unit.name,
                "isRefFlowProperty": True,
            },
        }


# =============================================================================
# CATEGORIA DE IMPACTO (ImpactCategory)
# =============================================================================
# Agrupa todos os fatores de caracterizacao de um mesmo tipo de impacto.
# Exemplos de categorias:
#   - "particulate matter formation - PMFP" (com fatores em DALY)
#   - "climate change - GWP100" (com fatores em kg CO2-Eq)
#   - "terrestrial acidification - TAP" (com fatores em mol H+-Eq)
#
# Uma categoria pode ter centenas de fatores (um por substancia+compartimento).
# No caso RAICV-Brazil, sao 725 fatores em uma unica categoria.
#
# method_category define se e "endpoint" (dano final, ex: DALY) ou "midpoint"
# (impacto intermediario, ex: kg CO2-Eq).
# =============================================================================

@dataclass
class ImpactCategoryDef:
    # Nome da categoria (ex: "particulate matter formation - PMFP")
    name: str
    # Descricao com detalhes e referencia bibliografica
    description: str
    # Unidade de referencia do impacto (ex: "DALY", "kg CO2-Eq")
    ref_unit: str
    # Tipo: "endpoint" (dano final) ou "midpoint" (impacto intermediario)
    method_category: str = "endpoint"
    uid: str = field(default_factory=new_uuid)
    # Lista de todos os fatores de caracterizacao desta categoria
    impact_factors: list[ImpactFactorDef] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Gera o JSON-LD da categoria com TODOS os fatores dentro do array.

        Este e o arquivo mais pesado do pacote — contem o array impactFactors[]
        com centenas de entradas. Cada entrada e um ImpactFactorDef.to_dict().
        """
        return {
            "@type": "ImpactCategory",
            "@id": self.uid,
            "name": self.name,
            "description": self.description,
            "refUnit": self.ref_unit,
            "category": self.method_category,
            # Array com TODOS os fatores — e aqui que esta o conteudo principal
            "impactFactors": [f.to_dict() for f in self.impact_factors],
        }


# =============================================================================
# METODO LCIA (ImpactMethod)
# =============================================================================
# E a entidade de nivel mais alto — o "pacote" que aparece na lista de metodos
# do OpenLCA. Um metodo pode conter varias categorias de impacto.
# Exemplos de metodos:
#   - "ReCiPe 2016 Midpoint (H)" (contem ~18 categorias)
#   - "RAICV-Brazil - PMFP" (contem 1 categoria: material particulado)
#
# No nosso caso, cada execucao gera um metodo com uma unica categoria.
# Para metodos com multiplas categorias, basta adicionar mais entradas na
# lista 'categories'.
# =============================================================================

@dataclass
class ImpactMethodDef:
    # Nome do metodo (ex: "RAICV-Brazil - PMFP")
    name: str
    # Descricao completa com referencia bibliografica
    description: str
    # Lista de categorias de impacto que este metodo contem
    categories: list[ImpactCategoryDef] = field(default_factory=list)
    # Versao do metodo
    version: str = "1.0"
    uid: str = field(default_factory=new_uuid)

    def to_dict(self) -> dict:
        """Gera o JSON-LD do metodo, referenciando cada categoria pelo UUID.

        Note que aqui NAO incluimos os fatores — apenas a referencia a cada
        categoria. Os fatores ficam no arquivo da propria categoria
        (lcia_categories/{uuid}.json).
        """
        return {
            "@type": "ImpactMethod",
            "@id": self.uid,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            # Referencia as categorias — o OpenLCA carrega os fatores de cada
            # categoria pelo @id correspondente na pasta lcia_categories/
            "impactCategories": [
                {
                    "@type": "ImpactCategory",
                    "@id": cat.uid,
                    "name": cat.name,
                    "category": cat.method_category,
                    "refUnit": cat.ref_unit,
                }
                for cat in self.categories
            ],
        }


# =============================================================================
# CONFIGURACAO DO METODO (MethodConfig)
# =============================================================================
# Representa todos os parametros que o usuario define no arquivo YAML.
# Esta classe e o "contrato" entre o config YAML e o motor de conversao —
# tudo que o converter.py precisa para executar esta aqui.
#
# Nenhum campo e opcional exceto reference_zip e model_zip (que permitem
# operar sem uma base de referencia).
# =============================================================================

@dataclass
class MethodConfig:
    """Representacao parseada de um arquivo de configuracao YAML.

    Campos:
        method_name: Nome do metodo LCIA (aparece no OpenLCA)
        method_description: Descricao com referencia bibliografica
        category_name: Nome da categoria de impacto
        category_description: Descricao da categoria
        category_type: "endpoint" ou "midpoint"
        input_unit_name: Unidade de entrada (ex: "kg")
        input_property_name: Propriedade de entrada (ex: "Mass")
        output_unit_name: Unidade de saida/impacto (ex: "DALY")
        output_property_name: Propriedade de saida (ex: "Impact on human health")
        excel_path: Caminho para a planilha com os CFs
        reference_zip: Caminho para o ZIP de referencia (Ecoinvent) — opcional
        model_zip: Caminho para o ZIP modelo (estrutura base) — opcional
        output_zip: Caminho para o ZIP de saida
        excel_columns: Mapeamento dos nomes das colunas do Excel
    """

    method_name: str
    method_description: str
    category_name: str
    category_description: str
    category_type: str  # endpoint | midpoint
    input_unit_name: str
    input_property_name: str
    output_unit_name: str
    output_property_name: str
    excel_path: str
    reference_zip: Optional[str]
    model_zip: Optional[str]
    output_zip: str
    # Mapeamento de nomes de colunas — permite usar planilhas com headers diferentes
    excel_columns: dict = field(default_factory=lambda: {
        "flow": "Flow",
        "category": "Category",
        "factor": "Factor",
        "unit": "Unit",
        "location": "Location",
    })
