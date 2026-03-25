# Examples

This directory contains example data files for the `olca-cf-converter`.

## Files

### Provided (from RAICV-Brazil case study)
- `CF-DALY-Giusti-Flows.xlsx` — Characterization factors for PM formation (Giusti 2025)
- `Base-Ecoinvent.zip` — Reference flows from Ecoinvent (for ID reuse)
- `RAICV-Brazil-modelo.zip` — Base model structure for OpenLCA

### How to add your own example
1. Copy your `.xlsx` file here
2. Create a config in `configs/` pointing to it
3. Run `olca-cf convert configs/your-config.yaml`

## Excel template

Your Excel must have these columns:

| Column | Type | Description |
|--------|------|-------------|
| Flow | text | Substance name (match Ecoinvent names for ID reuse) |
| Category | text | Full compartment path (e.g., "Elementary flows/Emission to air/unspecified") |
| Factor | number | Characterization factor value |
| Unit | text | Output unit (informational) |
| Location | text | Geographic location (for regionalized CFs) |
