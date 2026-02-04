# 🏭 Data Pipeline Documentation

This directory contains the automation for building the Sales Catalog from official Receita Federal data.

## 📂 Structure
- `pipeline.py`: Main orchestrator. Runs the full process.
- `download_receita.py`: Downloads raw CSVs from dados.gov.br.
- `filter_cnae.py`: Filters raw data by market segment (CNAE) and State.
- `import_to_db.py`: Imports filtered CSVs into the PostgreSQL database.

## 🚀 How to Run Locally

### 1. Full Pipeline (Recommended)
Process all segments for a specific state:
```bash
python -m app.data.pipeline --uf SP
```

Process specific segments:
```bash
python -m app.data.pipeline --uf RJ --segments restaurantes advocacia
```

### 2. Manual Steps
If you need granular control:
```bash
# Download
python -m app.data.download_receita

# Filter
python -m app.data.filter_cnae --segment tecnologia --uf SP

# Import
python -m app.data.import_to_db --input ./data/segments/tecnologia_SP.csv --segment "Tecnologia SP"
```

## 📊 Configured Segments
Check `filter_cnae.py` for the full list of CNAE codes per segment:
- Restaurantes
- Advocacia
- Contabilidade
- Clínicas Médicas
- Salões de Beleza
- Academias
- Imobiliárias
- Marketing
- Tecnologia
- Padarias

## 🤖 GitHub Actions
The workflow `.github/workflows/data_pipeline.yml` runs this pipeline automatically once a month to keep data fresh.
