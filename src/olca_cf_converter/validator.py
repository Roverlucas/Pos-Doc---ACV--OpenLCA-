"""
validator.py — Validacao de arquivos Excel e configuracoes YAML.

Este modulo e executado ANTES da conversao para garantir que os dados de
entrada estao corretos. Sem validacao, erros no Excel causariam falhas
silenciosas (fatores ignorados, ZIPs corrompidos, metodos vazios).

VALIDACOES REALIZADAS:
    1. Arquivo existe no disco
    2. Extensao e .xlsx ou .xls
    3. Pandas consegue ler o arquivo
    4. Todas as colunas obrigatorias estao presentes
    5. Coluna Factor contem apenas valores numericos
    6. Coluna Flow nao tem celulas vazias

POR QUE VALIDAR?
    Um erro comum e o pesquisador salvar o Excel com colunas fora de ordem
    ou com nomes diferentes (ex: "Substance" em vez de "Flow"). Sem validacao,
    o script rodaria sem erro mas geraria um ZIP vazio ou com fatores zerados.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


# Nomes padrao das colunas que o Excel deve conter.
# Podem ser alterados pelo usuario no YAML (secao "columns:").
REQUIRED_COLUMNS_DEFAULT = ["Flow", "Category", "Factor", "Unit", "Location"]


class ValidationError(Exception):
    """Erro lancado quando a validacao de entrada falha.

    Mensagens sao claras e indicam exatamente o problema e como corrigir.
    """
    pass


# =============================================================================
# VALIDACAO DO EXCEL
# =============================================================================
# Funcao principal de validacao. Recebe o caminho do arquivo .xlsx e a lista
# de colunas obrigatorias. Retorna um DataFrame validado ou lanca erro.
# =============================================================================

def validate_excel(
    path: str | Path,
    required_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Valida e carrega um arquivo Excel com fatores de caracterizacao.

    Args:
        path: Caminho para o arquivo .xlsx ou .xls
        required_columns: Lista de nomes de colunas obrigatorias.
                         Se None, usa o padrao: Flow, Category, Factor, Unit, Location.

    Returns:
        DataFrame do pandas com os dados validados.

    Raises:
        ValidationError: Se qualquer validacao falhar.
    """
    path = Path(path)
    cols = required_columns or REQUIRED_COLUMNS_DEFAULT

    # --- Verificacao 1: O arquivo existe? ---
    if not path.exists():
        raise ValidationError(f"File not found: {path}")

    # --- Verificacao 2: A extensao e valida? ---
    # Aceitamos .xlsx (Excel moderno) e .xls (Excel legado)
    if path.suffix not in (".xlsx", ".xls"):
        raise ValidationError(f"Expected .xlsx or .xls, got: {path.suffix}")

    # --- Verificacao 3: O pandas consegue ler o arquivo? ---
    # Pode falhar se o arquivo estiver corrompido, protegido por senha, etc.
    try:
        df = pd.read_excel(path)
    except Exception as e:
        raise ValidationError(f"Cannot read Excel file: {e}") from e

    # --- Verificacao 4: Todas as colunas obrigatorias existem? ---
    # Compara os nomes esperados com os nomes reais do Excel
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValidationError(
            f"Missing required columns: {missing}. "
            f"Found: {list(df.columns)}. "
            f"Expected: {cols}"
        )

    # --- Verificacao 5: A coluna Factor contem apenas numeros? ---
    # Valores como "N/A", "-", ou celulas com texto causam erros na conversao
    factor_col = cols[2]  # "Factor" por padrao
    non_numeric = df[~df[factor_col].apply(lambda x: isinstance(x, (int, float)))]
    if len(non_numeric) > 0:
        raise ValidationError(
            f"Non-numeric values in '{factor_col}' column at rows: "
            f"{list(non_numeric.index[:5])}..."
        )

    # --- Verificacao 6: A coluna Flow nao tem celulas vazias? ---
    # Um flow sem nome geraria um JSON invalido
    empty_flows = df[df[cols[0]].isna() | (df[cols[0]].astype(str).str.strip() == "")]
    if len(empty_flows) > 0:
        raise ValidationError(
            f"Empty flow names at rows: {list(empty_flows.index[:5])}..."
        )

    return df


# =============================================================================
# VALIDACAO DOS CAMINHOS DO CONFIG
# =============================================================================
# Verifica se os arquivos referenciados no YAML existem no disco.
# O arquivo Excel e obrigatorio — os ZIPs de referencia e modelo sao opcionais.
# =============================================================================

def validate_config_paths(config: dict) -> list[str]:
    """Verifica se os caminhos de arquivo do config YAML existem.

    Args:
        config: Dicionario com o conteudo do YAML parseado.

    Returns:
        Lista de warnings (strings) para arquivos opcionais nao encontrados.

    Raises:
        ValidationError: Se o arquivo Excel (obrigatorio) nao for encontrado.
    """
    warnings = []
    files_section = config.get("files", {})

    for key in ("excel", "reference_zip", "model_zip"):
        val = files_section.get(key)
        if val and not Path(val).exists():
            if key == "reference_zip":
                # reference_zip e opcional — sem ele, UUIDs novos sao gerados
                warnings.append(f"Reference ZIP not found: {val} (will generate new IDs)")
            elif key == "model_zip":
                # model_zip e opcional — sem ele, a estrutura e criada do zero
                warnings.append(f"Model ZIP not found: {val} (will create structure from scratch)")
            else:
                # excel e OBRIGATORIO — sem ele, nao ha o que converter
                raise ValidationError(f"Required file not found: {val} (key: files.{key})")

    return warnings


# =============================================================================
# RELATORIO DE VALIDACAO
# =============================================================================
# Imprime um resumo dos dados carregados para o usuario confirmar visualmente
# que o Excel foi lido corretamente (numero de substancias, regioes, etc.).
# =============================================================================

def print_validation_report(df: pd.DataFrame) -> None:
    """Imprime um resumo dos dados do Excel validado.

    Util para o usuario confirmar rapidamente que o arquivo foi lido
    corretamente antes de iniciar a conversao.
    """
    flow_col, cat_col, factor_col, unit_col, loc_col = (
        "Flow", "Category", "Factor", "Unit", "Location"
    )

    print(f"  Rows:        {len(df)}")
    print(f"  Flows:       {df[flow_col].nunique()} unique substances")
    print(f"  Categories:  {df[cat_col].nunique()} compartments")
    print(f"  Locations:   {df[loc_col].nunique()} regions")
    print(f"  Unit:        {df[unit_col].iloc[0] if len(df) > 0 else 'N/A'}")
    print(f"  Factor range: {df[factor_col].min():.6e} to {df[factor_col].max():.6e}")
