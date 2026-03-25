"""
converter.py — Motor de conversao: Excel -> pacote OpenLCA JSON-LD (ZIP).

Este e o modulo central do olca-cf-converter. Ele orquestra todo o pipeline
de conversao em 12 passos sequenciais:

    [Excel .xlsx] --> [Validacao] --> [Criacao de entidades] --> [ZIP final]

PIPELINE COMPLETO:
    Step 1:  Extrair estrutura base do modelo (opcional)
    Step 2:  Carregar IDs de referencia do Ecoinvent (opcional)
    Step 3:  Ler e validar a planilha Excel
    Step 4:  Criar unidades de entrada (ex: kg)
    Step 5:  Criar unidades de saida (ex: DALY)
    Step 6:  Escrever arquivos JSON de unidades, grupos e propriedades
    Step 7:  Criar flows (substancias), reusando IDs quando possivel
    Step 8:  Construir mapa de UUIDs (nome, categoria, localizacao) -> UUID
    Step 9:  Criar categoria de impacto com todos os fatores de caracterizacao
    Step 10: Criar metodo LCIA
    Step 11: Escrever manifesto openlca.json
    Step 12: Empacotar tudo em um ZIP

O resultado e um arquivo .zip que pode ser importado diretamente no OpenLCA
via File -> Import -> Linked Data (JSON-LD).
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path

import pandas as pd

# Importamos as classes de schemas.py que representam as entidades do OpenLCA
from .schemas import (
    FlowDef,
    FlowPropertyDef,
    ImpactCategoryDef,
    ImpactFactorDef,
    ImpactMethodDef,
    MethodConfig,
    UnitDef,
    UnitGroupDef,
    new_uuid,
)
from .validator import validate_excel


# =============================================================================
# FUNCAO AUXILIAR: ESCREVER JSON
# =============================================================================
# No OpenLCA, cada entidade e salva como um arquivo {uuid}.json dentro da
# pasta correspondente (ex: flows/9990b51b-7023-....json). Esta funcao
# simplifica essa operacao.
# =============================================================================

def _write_json(directory: Path, uid: str, data: dict) -> None:
    """Escreve um arquivo JSON nomeado {uid}.json dentro do diretorio.

    Args:
        directory: Pasta onde o arquivo sera criado (ex: flows/, units/)
        uid: UUID da entidade — sera o nome do arquivo
        data: Dicionario Python que sera serializado como JSON
    """
    path = directory / f"{uid}.json"
    with open(path, "w", encoding="utf-8") as f:
        # indent=2 para legibilidade; ensure_ascii=False para acentos
        json.dump(data, f, indent=2, ensure_ascii=False)


# =============================================================================
# FUNCAO AUXILIAR: CARREGAR FLOWS DE REFERENCIA (ECOINVENT)
# =============================================================================
# Esta funcao e o SEGREDO para que os fatores de caracterizacao funcionem com
# inventarios existentes no OpenLCA. Ela le os flows de um ZIP de referencia
# (tipicamente uma exportacao do Ecoinvent) e extrai os UUIDs.
#
# COMO FUNCIONA O MATCHING:
#   Para cada flow no ZIP de referencia, guardamos a tupla (nome, categoria)
#   e o UUID correspondente. Depois, quando criamos os flows do nosso metodo,
#   verificamos se a mesma tupla (nome, categoria) existe no mapa. Se existir,
#   REUSAMOS o UUID do Ecoinvent em vez de gerar um novo.
#
# POR QUE ISSO E CRITICO:
#   O OpenLCA conecta fatores de caracterizacao a processos do inventario
#   PELO UUID, nao pelo nome. Se o UUID nao bater, o fator nao e aplicado —
#   mesmo que o nome da substancia seja identico.
# =============================================================================

def _load_reference_flows(ref_zip: str | Path | None) -> dict[tuple[str, str], str]:
    """Carrega UUIDs de flows existentes de um ZIP de referencia.

    Args:
        ref_zip: Caminho para o ZIP (ou diretorio) com flows de referencia.
                 Tipicamente uma exportacao JSON-LD do Ecoinvent.
                 Se None, retorna dict vazio (todos os IDs serao novos).

    Returns:
        Dicionario mapeando (nome_do_flow, categoria) -> UUID existente.
        Exemplo: ("Ammonia", "Elementary flows/Emission to air/unspecified") -> "9990b51b-..."
    """
    # Se nao foi fornecido um ZIP de referencia, nao ha IDs para reusar
    if ref_zip is None:
        return {}

    ref_zip = Path(ref_zip)
    if not ref_zip.exists():
        print(f"  ⚠ Reference ZIP not found: {ref_zip}. Generating new IDs.")
        return {}

    existing: dict[tuple[str, str], str] = {}
    # Pasta temporaria para extrair o ZIP — usa PID para evitar colisoes
    ref_dir = Path(f"_ref_temp_{os.getpid()}")

    try:
        # Aceita tanto ZIP quanto diretorio ja extraido
        if ref_zip.is_dir():
            search_root = ref_zip
        else:
            # Extrai o ZIP para pasta temporaria
            shutil.rmtree(ref_dir, ignore_errors=True)
            ref_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(ref_zip, "r") as zf:
                zf.extractall(ref_dir)
            search_root = ref_dir

        # Busca a pasta "flows/" — pode estar na raiz ou dentro de uma subpasta
        # (ex: Base-Ecoinvent/flows/ quando o ZIP foi criado a partir de um diretorio)
        flows_dir = search_root / "flows"
        if not flows_dir.is_dir():
            # Busca recursivamente por uma pasta chamada "flows" com arquivos JSON
            for candidate in search_root.rglob("flows"):
                if candidate.is_dir() and any(candidate.glob("*.json")):
                    flows_dir = candidate
                    break

        if not flows_dir.is_dir():
            print(f"  ⚠ No 'flows/' folder in reference. Generating new IDs.")
            return {}

        # Le cada arquivo JSON na pasta flows/ e extrai (nome, categoria) -> UUID
        for fn in flows_dir.iterdir():
            if fn.suffix != ".json":
                continue
            try:
                with open(fn, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Verifica se e realmente um Flow (e nao outro tipo de entidade)
                if data.get("@type") == "Flow":
                    name = data.get("name")
                    cat = data.get("category")
                    fid = data.get("@id")
                    if name and cat and fid:
                        # setdefault: se ja existe, nao sobrescreve (primeiro encontrado ganha)
                        existing.setdefault((name, cat), fid)
            except Exception:
                # Ignora arquivos com problemas (corrompidos, formato errado)
                continue

        print(f"  ✓ Loaded {len(existing)} reference flow IDs")
    finally:
        # SEMPRE limpa a pasta temporaria, mesmo se der erro
        if ref_dir.exists() and not ref_zip.is_dir():
            shutil.rmtree(ref_dir, ignore_errors=True)

    return existing


# =============================================================================
# FUNCAO AUXILIAR: EXTRAIR ESTRUTURA BASE DO MODELO
# =============================================================================
# Alguns metodos LCIA partem de uma estrutura base (modelo) que ja contem
# pastas e o arquivo openlca.json. Esta funcao extrai essa base para a pasta
# temporaria de trabalho. Se nao houver modelo, a estrutura e criada do zero.
# =============================================================================

def _extract_model_base(model_zip: str | Path | None, temp_dir: Path) -> None:
    """Extrai o ZIP modelo como estrutura base, ou cria do zero.

    Args:
        model_zip: Caminho para o ZIP modelo (ou None para criar do zero)
        temp_dir: Pasta temporaria onde a estrutura sera montada
    """
    if model_zip is None:
        return

    model_zip = Path(model_zip)
    if not model_zip.exists():
        print(f"  ⚠ Model ZIP not found: {model_zip}. Creating structure from scratch.")
        return

    # Aceita tanto ZIP quanto diretorio
    if model_zip.is_dir():
        for item in model_zip.iterdir():
            dest = temp_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
    else:
        with zipfile.ZipFile(model_zip, "r") as zf:
            zf.extractall(temp_dir)

    # Se o ZIP tinha uma pasta-raiz (ex: RAICV-Brazil-modelo/), move o conteudo
    # para a raiz do temp_dir para manter a estrutura plana que o OpenLCA espera
    subdirs = [d for d in temp_dir.iterdir() if d.is_dir()]
    if len(subdirs) == 1 and (subdirs[0] / "openlca.json").exists():
        wrapper = subdirs[0]
        for item in wrapper.iterdir():
            dest = temp_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        shutil.rmtree(wrapper)

    print(f"  ✓ Base structure loaded from model")


# =============================================================================
# FUNCAO PRINCIPAL: CONVERTER
# =============================================================================
# Orquestra os 12 passos do pipeline. Recebe um MethodConfig (parseado do
# YAML) e retorna o caminho do ZIP gerado.
#
# A funcao trabalha em uma pasta temporaria (_olca_build_{pid}/) que e SEMPRE
# removida ao final, mesmo em caso de erro (bloco finally).
# =============================================================================

def convert(config: MethodConfig) -> Path:
    """Executa o pipeline completo de conversao.

    Args:
        config: MethodConfig com todos os parametros (parseado do YAML).

    Returns:
        Path para o arquivo ZIP gerado, pronto para importar no OpenLCA.
    """
    output_path = Path(config.output_zip)
    # Pasta temporaria com PID para evitar colisoes entre execucoes paralelas
    temp_dir = Path(f"_olca_build_{os.getpid()}")

    try:
        # Limpa qualquer resto de execucao anterior
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(exist_ok=True)

        # =================================================================
        # STEP 1: Extrair estrutura base do modelo (opcional)
        # =================================================================
        # Se o usuario forneceu um model_zip, extrai como ponto de partida.
        # Isso permite herdar configuracoes ou estruturas pre-existentes.
        _extract_model_base(config.model_zip, temp_dir)

        # =================================================================
        # STEP 2: Carregar IDs de referencia para reuso (opcional)
        # =================================================================
        # Le os UUIDs dos flows do Ecoinvent (ou outra base) para que os
        # nossos flows usem os MESMOS UUIDs — garantindo compatibilidade.
        existing_flows = _load_reference_flows(config.reference_zip)

        # =================================================================
        # STEP 3: Ler e validar a planilha Excel
        # =================================================================
        # A validacao verifica colunas, tipos numericos e nomes nao vazios
        # ANTES de iniciar a conversao (fail-fast).
        col = config.excel_columns
        df = validate_excel(
            config.excel_path,
            required_columns=[col["flow"], col["category"], col["factor"], col["unit"], col["location"]],
        )
        print(f"  ✓ Loaded {len(df)} characterization factors from Excel")

        # =================================================================
        # STEP 4: Criar unidades de ENTRADA
        # =================================================================
        # A unidade de entrada e aquela em que a emissao e medida.
        # Tipicamente "kg" (massa emitida ao ambiente).
        # Criamos a cadeia completa: Unit -> UnitGroup -> FlowProperty
        input_unit = UnitDef(name=config.input_unit_name)
        input_unit_group = UnitGroupDef(
            name=f"{config.input_property_name} units",
            unit=input_unit,
        )
        input_flow_property = FlowPropertyDef(
            name=config.input_property_name,
            unit_group=input_unit_group,
        )

        # =================================================================
        # STEP 5: Criar unidades de SAIDA (impacto)
        # =================================================================
        # A unidade de saida e aquela em que o impacto e medido.
        # Exemplos: "DALY" (anos de vida perdidos), "kg CO2-Eq", "CTUe"
        # A categoria muda conforme o tipo: endpoint usa "Impact category
        # indicators", midpoint usa "Technical unit groups".
        output_unit = UnitDef(name=config.output_unit_name)
        output_unit_group = UnitGroupDef(
            name=f"{config.output_property_name} units",
            unit=output_unit,
            category="Impact category indicators" if config.category_type == "endpoint" else "Technical unit groups",
        )
        output_flow_property = FlowPropertyDef(
            name=config.output_property_name,
            unit_group=output_unit_group,
            category="Impact category indicators" if config.category_type == "endpoint" else "Technical flow properties",
        )

        # =================================================================
        # STEP 6: Escrever arquivos JSON de unidades, grupos e propriedades
        # =================================================================
        # Cria as 6 pastas que o OpenLCA espera encontrar no ZIP e escreve
        # os arquivos JSON de cada entidade de suporte.

        # Mapa de pastas do pacote OpenLCA
        dirs = {
            "units": temp_dir / "units",                    # Unidades (kg, DALY)
            "unit_groups": temp_dir / "unit_groups",        # Grupos de unidades
            "flow_properties": temp_dir / "flow_properties",# Propriedades de fluxo
            "flows": temp_dir / "flows",                    # Substancias (Ammonia, NOx)
            "lcia_categories": temp_dir / "lcia_categories",# Categorias de impacto
            "lcia_methods": temp_dir / "lcia_methods",      # Metodos LCIA
        }
        # Recria cada pasta do zero (garante estado limpo)
        for d in dirs.values():
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)

        # --- Escrever unidades ---
        # Cada unidade e salva como {uuid}.json na pasta units/
        _write_json(dirs["units"], input_unit.uid, {
            "@type": "Unit", "@id": input_unit.uid,
            "name": input_unit.name, "referenceUnitName": input_unit.name,
            "synonyms": [], "internalId": None, "default": True,
        })
        _write_json(dirs["units"], output_unit.uid, {
            "@type": "Unit", "@id": output_unit.uid,
            "name": output_unit.name, "referenceUnitName": output_unit.name,
            "synonyms": [], "internalId": None, "default": True,
        })

        # --- Escrever grupos de unidades ---
        _write_json(dirs["unit_groups"], input_unit_group.uid, input_unit_group.to_dict())
        _write_json(dirs["unit_groups"], output_unit_group.uid, output_unit_group.to_dict())

        # --- Escrever propriedades de fluxo ---
        _write_json(dirs["flow_properties"], input_flow_property.uid, input_flow_property.to_dict())
        _write_json(dirs["flow_properties"], output_flow_property.uid, output_flow_property.to_dict())

        # =================================================================
        # STEP 7: Criar flows (substancias), reusando IDs quando possivel
        # =================================================================
        # Para cada combinacao unica de (nome, categoria) na planilha:
        #   1. Verifica se existe no mapa de referencia (Ecoinvent)
        #   2. Se sim: reutiliza o UUID (compatibilidade com inventarios)
        #   3. Se nao: gera um novo UUID
        #   4. Escreve o arquivo JSON do flow
        #
        # IMPORTANTE: Deduplicamos por (nome, categoria), NAO por
        # (nome, categoria, localizacao). A mesma substancia no mesmo
        # compartimento em localizacoes diferentes e o MESMO flow.
        # A regionalizacao acontece no nivel do fator, nao do flow.

        unique_flows = df[[col["flow"], col["category"]]].drop_duplicates()
        name_cat_to_id: dict[tuple[str, str], str] = {}

        for _, row in unique_flows.iterrows():
            flow_name = row[col["flow"]]
            category = row[col["category"]]
            key = (flow_name, category)

            # Tenta reusar UUID do Ecoinvent; se nao encontrar, gera novo
            flow_id = existing_flows.get(key, new_uuid())
            name_cat_to_id[key] = flow_id

            # Cria o objeto FlowDef e escreve como JSON
            flow_def = FlowDef(
                name=flow_name,
                category=category,
                flow_property=input_flow_property,
                uid=flow_id,
            )
            _write_json(dirs["flows"], flow_id, flow_def.to_dict())

        # Relatorio de reuso
        reused = sum(1 for k in name_cat_to_id if k in existing_flows)
        created = len(name_cat_to_id) - reused
        print(f"  ✓ Flows: {reused} reused IDs + {created} new = {len(name_cat_to_id)} total")

        # =================================================================
        # STEP 8: Construir mapa completo (nome, categoria, localizacao) -> UUID
        # =================================================================
        # Este mapa expande o anterior para incluir a localizacao. Ele sera
        # usado no Step 9 para conectar cada linha do Excel ao flow correto.
        # Multiplas localizacoes apontam para o MESMO UUID de flow.
        flow_uuid_map: dict[tuple[str, str, str], str] = {}
        unique_full = df[[col["flow"], col["category"], col["location"]]].drop_duplicates()
        for _, row in unique_full.iterrows():
            key_nc = (row[col["flow"]], row[col["category"]])
            fid = name_cat_to_id.get(key_nc)
            if fid:
                flow_uuid_map[(row[col["flow"]], row[col["category"]], row[col["location"]])] = fid

        # =================================================================
        # STEP 9: Criar categoria de impacto com TODOS os fatores
        # =================================================================
        # Aqui e onde o conteudo principal e montado. Para CADA LINHA do
        # Excel, criamos um ImpactFactorDef com:
        #   - O valor numerico do CF
        #   - A referencia ao flow (pelo UUID)
        #   - A unidade e propriedade de entrada
        #
        # Todos os fatores ficam dentro de um unico ImpactCategoryDef.
        impact_category = ImpactCategoryDef(
            name=config.category_name,
            description=config.category_description,
            ref_unit=config.output_unit_name,
            method_category=config.category_type,
        )

        skipped = 0
        for _, row in df.iterrows():
            key = (row[col["flow"]], row[col["category"]], row[col["location"]])
            flow_id = flow_uuid_map.get(key)

            # Se nao encontrou UUID para esta linha, pula (e conta como skipped)
            if not flow_id:
                skipped += 1
                continue

            # Cria a referencia ao flow usando o UUID correto
            key_nc = (row[col["flow"]], row[col["category"]])
            flow_def = FlowDef(
                name=row[col["flow"]],
                category=row[col["category"]],
                flow_property=input_flow_property,
                uid=name_cat_to_id[key_nc],
            )

            # Adiciona o fator de caracterizacao a categoria
            impact_category.impact_factors.append(
                ImpactFactorDef(
                    value=float(row[col["factor"]]),
                    flow=flow_def,
                    input_unit=input_unit,
                    input_flow_property=input_flow_property,
                )
            )

        if skipped > 0:
            print(f"  ⚠ Skipped {skipped} unmapped factors")

        # Escreve o JSON da categoria (contem o array impactFactors[] completo)
        _write_json(dirs["lcia_categories"], impact_category.uid, impact_category.to_dict())
        print(f"  ✓ Impact category: {len(impact_category.impact_factors)} factors")

        # =================================================================
        # STEP 10: Criar metodo LCIA
        # =================================================================
        # O metodo e a entidade de nivel mais alto — e o que aparece na lista
        # de metodos do OpenLCA. Ele referencia a(s) categoria(s) pelo UUID.
        method = ImpactMethodDef(
            name=config.method_name,
            description=config.method_description,
            categories=[impact_category],
        )
        _write_json(dirs["lcia_methods"], method.uid, method.to_dict())
        print(f"  ✓ Method: {config.method_name}")

        # =================================================================
        # STEP 11: Escrever manifesto openlca.json
        # =================================================================
        # O arquivo openlca.json DEVE estar na RAIZ do ZIP. Sem ele, o
        # OpenLCA nao reconhece o pacote como importavel.
        # schemaVersion: 2 e a versao atual do formato JSON-LD do OpenLCA.
        _write_json(temp_dir, "openlca", {"schemaVersion": 2})
        # Corrige o nome do arquivo (deve ser exatamente "openlca.json")
        for f in temp_dir.glob("openlca*.json"):
            f.unlink()
        with open(temp_dir / "openlca.json", "w") as f:
            json.dump({"schemaVersion": 2}, f)

        # =================================================================
        # STEP 12: Empacotar tudo em ZIP
        # =================================================================
        # Percorre recursivamente a pasta temporaria e adiciona cada arquivo
        # ao ZIP com o caminho relativo correto (ex: flows/abc-123.json).
        # Usa compressao ZIP_DEFLATED para reduzir o tamanho.
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    full = Path(root) / file
                    # arcname = caminho dentro do ZIP (relativo a raiz)
                    arcname = full.relative_to(temp_dir)
                    zf.write(full, arcname)

        # Conta quantos arquivos ficaram no ZIP para o relatorio
        with zipfile.ZipFile(output_path, "r") as zf:
            file_count = len(zf.namelist())

        print(f"  ✓ Output: {output_path} ({file_count} files)")

    finally:
        # SEMPRE remove a pasta temporaria, mesmo se der erro no meio
        # Isso evita lixo no disco do usuario
        shutil.rmtree(temp_dir, ignore_errors=True)

    return output_path
