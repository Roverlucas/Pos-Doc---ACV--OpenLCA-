"""
cli.py — Interface de linha de comando do olca-cf-converter.

Este modulo e o ponto de entrada do programa. Ele interpreta os argumentos
da linha de comando e despacha para a funcao correta.

COMANDOS DISPONIVEIS:
    olca-cf convert config.yaml    Converte Excel -> ZIP do OpenLCA
    olca-cf validate data.xlsx     Valida um arquivo Excel
    olca-cf init                   Gera um template de config YAML

COMO FUNCIONA:
    1. O usuario digita um comando no terminal
    2. argparse interpreta os argumentos
    3. O comando e despachado para cmd_convert(), cmd_validate() ou cmd_init()
    4. Cada funcao orquestra a operacao correspondente

RESOLUCAO DE CAMINHOS:
    Todos os caminhos no YAML sao resolvidos RELATIVAMENTE ao diretorio
    onde o arquivo config esta. Exemplo:
        Se o config esta em /projeto/configs/meu.yaml
        e o excel diz "../data/fatores.xlsx"
        o caminho resolvido sera /projeto/data/fatores.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import __version__
from .converter import convert
from .schemas import MethodConfig
from .validator import (
    ValidationError,
    print_validation_report,
    validate_config_paths,
    validate_excel,
)


# =============================================================================
# CARREGAR CONFIGURACAO YAML
# =============================================================================
# Le o arquivo YAML e converte para um objeto MethodConfig que o motor de
# conversao (converter.py) entende. Aqui e onde os caminhos relativos sao
# resolvidos para caminhos absolutos.
# =============================================================================

def _load_config(config_path: str) -> MethodConfig:
    """Faz o parsing do arquivo YAML e retorna um MethodConfig.

    Args:
        config_path: Caminho para o arquivo .yaml de configuracao.

    Returns:
        MethodConfig preenchido com todos os parametros.
    """
    path = Path(config_path)
    if not path.exists():
        print(f"✗ Config file not found: {path}")
        sys.exit(1)

    # Le o YAML usando yaml.safe_load (seguro contra injecao de codigo)
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Diretorio do config — sera a base para resolver caminhos relativos
    config_dir = path.parent

    # --- Extrair secao "files" ---
    files = raw.get("files", {})
    excel = files.get("excel", "")
    ref_zip = files.get("reference_zip")
    model_zip = files.get("model_zip")
    output_zip = files.get("output_zip", "output.zip")

    def resolve(p):
        """Converte caminho relativo para absoluto baseado no diretorio do config.

        Se o caminho ja for absoluto, retorna como esta.
        Se for None, retorna None (para campos opcionais).
        """
        if p is None:
            return None
        pp = Path(p)
        if not pp.is_absolute():
            pp = config_dir / pp
        return str(pp)

    # --- Extrair secoes do YAML ---
    method = raw.get("method", {})
    category = raw.get("category", {})
    units = raw.get("units", {})
    inp = units.get("input", {})
    out = units.get("output", {})

    # --- Mapeamento de colunas ---
    # Permite que o usuario use nomes de colunas diferentes no Excel.
    # Se nao especificado, usa os nomes padrao (Flow, Category, Factor, Unit, Location)
    columns = raw.get("columns", {})
    col_map = {
        "flow": columns.get("flow", "Flow"),
        "category": columns.get("category", "Category"),
        "factor": columns.get("factor", "Factor"),
        "unit": columns.get("unit", "Unit"),
        "location": columns.get("location", "Location"),
    }

    # Monta o MethodConfig com todos os parametros resolvidos
    return MethodConfig(
        method_name=method.get("name", "Unnamed Method"),
        method_description=method.get("description", ""),
        category_name=category.get("name", "Unnamed Category"),
        category_description=category.get("description", ""),
        category_type=category.get("type", "endpoint"),
        input_unit_name=inp.get("name", "kg"),
        input_property_name=inp.get("property", "Mass"),
        output_unit_name=out.get("name", "DALY"),
        output_property_name=out.get("property", "Impact on human health"),
        excel_path=resolve(excel),
        reference_zip=resolve(ref_zip),
        model_zip=resolve(model_zip),
        output_zip=resolve(output_zip),
        excel_columns=col_map,
    )


# =============================================================================
# COMANDO: CONVERT
# =============================================================================
# Comando principal — le o config, valida os caminhos e executa a conversao.
# E acionado quando o usuario digita: olca-cf convert config.yaml
# =============================================================================

def cmd_convert(args: argparse.Namespace) -> None:
    """Executa o pipeline de conversao Excel -> ZIP do OpenLCA."""

    # Banner com versao
    print(f"{'='*60}")
    print(f"  olca-cf-converter v{__version__}")
    print(f"{'='*60}")
    print()

    # Carrega e mostra a configuracao
    config = _load_config(args.config)

    print(f"  Method:   {config.method_name}")
    print(f"  Category: {config.category_name}")
    print(f"  Units:    {config.input_unit_name} → {config.output_unit_name}")
    print(f"  Excel:    {config.excel_path}")
    print()

    # Valida que os arquivos referenciados existem
    with open(args.config, "r") as f:
        raw = yaml.safe_load(f)
    warnings = validate_config_paths(raw)
    for w in warnings:
        print(f"  ⚠ {w}")

    print("  Converting...")
    print()

    # Executa a conversao (os 12 steps do converter.py)
    try:
        output = convert(config)
        print()
        print(f"  ✅ Done! Import this file into OpenLCA:")
        print(f"     {output}")
        print()
        print(f"  OpenLCA: File → Import → JSON-LD → select the ZIP")
    except ValidationError as e:
        print(f"\n  ✗ Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ✗ Conversion failed: {e}")
        sys.exit(1)


# =============================================================================
# COMANDO: VALIDATE
# =============================================================================
# Valida um arquivo Excel SEM converter. Util para verificar se a planilha
# esta correta antes de rodar a conversao completa.
# Acionado por: olca-cf validate meu-arquivo.xlsx
# =============================================================================

def cmd_validate(args: argparse.Namespace) -> None:
    """Valida um arquivo Excel com fatores de caracterizacao."""
    print(f"  Validating: {args.excel}")
    print()

    try:
        # Roda todas as verificacoes (colunas, tipos, vazios)
        df = validate_excel(args.excel)
        # Mostra resumo dos dados carregados
        print_validation_report(df)
        print()
        print("  ✅ Excel file is valid!")
    except ValidationError as e:
        print(f"  ✗ {e}")
        sys.exit(1)


# =============================================================================
# COMANDO: INIT
# =============================================================================
# Gera um arquivo config YAML template para o usuario preencher.
# Util para quem esta comecando e nao sabe a estrutura do YAML.
# Acionado por: olca-cf init -o meu-config.yaml
# =============================================================================

def cmd_init(args: argparse.Namespace) -> None:
    """Gera um arquivo de configuracao YAML template."""

    # Template com valores padrao e comentarios implicitos nos nomes
    template = {
        "method": {
            "name": "My LCIA Method",
            "description": "Description of the method, including citation.",
        },
        "category": {
            "name": "impact category name",
            "description": "Description of this impact category.",
            "type": "endpoint",
        },
        "units": {
            "input": {"name": "kg", "property": "Mass"},
            "output": {"name": "DALY", "property": "Impact on human health"},
        },
        "files": {
            "excel": "my-factors.xlsx",
            "reference_zip": "Base-Ecoinvent.zip",
            "model_zip": None,
            "output_zip": "My-Method-FINAL.zip",
        },
        "columns": {
            "flow": "Flow",
            "category": "Category",
            "factor": "Factor",
            "unit": "Unit",
            "location": "Location",
        },
    }

    output = Path(args.output) if args.output else Path("config.yaml")

    # Protege contra sobrescrever config existente (a menos que --force)
    if output.exists() and not args.force:
        print(f"  ✗ {output} already exists. Use --force to overwrite.")
        sys.exit(1)

    # Escreve o YAML formatado
    with open(output, "w", encoding="utf-8") as f:
        yaml.dump(template, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"  ✅ Template config created: {output}")
    print()
    print("  Next steps:")
    print("  1. Edit the config with your method details")
    print("  2. Prepare your Excel with columns: Flow, Category, Factor, Unit, Location")
    print(f"  3. Run: olca-cf convert {output}")


# =============================================================================
# PONTO DE ENTRADA (main)
# =============================================================================
# Define os 3 subcomandos (convert, validate, init) usando argparse.
# Quando o usuario digita "olca-cf" sem argumentos, mostra o help.
# =============================================================================

def main() -> None:
    """Ponto de entrada principal da CLI."""

    # Parser principal
    parser = argparse.ArgumentParser(
        prog="olca-cf",
        description="Convert characterization factor spreadsheets into OpenLCA JSON-LD packages.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Subcomandos
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # --- Subcomando: convert ---
    p_convert = sub.add_parser("convert", help="Convert Excel → OpenLCA ZIP")
    p_convert.add_argument("config", help="Path to YAML config file")

    # --- Subcomando: validate ---
    p_validate = sub.add_parser("validate", help="Validate an Excel file")
    p_validate.add_argument("excel", help="Path to Excel file (.xlsx)")

    # --- Subcomando: init ---
    p_init = sub.add_parser("init", help="Generate template config file")
    p_init.add_argument("-o", "--output", help="Output path (default: config.yaml)")
    p_init.add_argument("--force", action="store_true", help="Overwrite if exists")

    args = parser.parse_args()

    # Se nenhum comando foi dado, mostra o help
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Despacha para a funcao do comando correspondente
    commands = {
        "convert": cmd_convert,
        "validate": cmd_validate,
        "init": cmd_init,
    }
    commands[args.command](args)


# Permite rodar diretamente: python -m olca_cf_converter.cli
if __name__ == "__main__":
    main()
