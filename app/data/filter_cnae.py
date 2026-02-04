"""
CNAE Filter - Filter Receita Federal data by CNAE codes

Reads the raw CSV files and filters by:
- CNAE (business activity code)
- UF (state)  
- Situação Cadastral (ATIVA)

Usage:
    python -m app.data.filter_cnae --cnae 5611201 --uf SP --output filtered.csv
"""

import csv
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

# CNAE codes for common segments
CNAE_SEGMENTS = {
    "restaurantes": ["5611201", "5611202", "5611203"],
    "padarias": ["1091101", "4721102"],
    "advocacia": ["6911701", "6911702"],
    "contabilidade": ["6920601", "6920602"],
    "clinicas_medicas": ["8630501", "8630502", "8630503"],
    "saloes_beleza": ["9602501", "9602502"],
    "academias": ["9313100"],
    "imobiliarias": ["6821801", "6821802"],
    "marketing": ["7311400", "7312200"],
    "tecnologia": ["6201501", "6201502", "6202300", "6203100"],
}

# UF codes
UF_CODES = {
    "AC": "12", "AL": "27", "AP": "16", "AM": "13", "BA": "29",
    "CE": "23", "DF": "53", "ES": "32", "GO": "52", "MA": "21",
    "MT": "51", "MS": "50", "MG": "31", "PA": "15", "PB": "25",
    "PR": "41", "PE": "26", "PI": "22", "RJ": "33", "RN": "24",
    "RS": "43", "RO": "11", "RR": "14", "SC": "42", "SP": "35",
    "SE": "28", "TO": "17"
}

@dataclass
class FilterConfig:
    cnae_codes: List[str]
    uf: Optional[str] = None
    situacao: str = "02"  # 02 = ATIVA
    limit: Optional[int] = None

def filter_estabelecimentos(
    input_file: str,
    config: FilterConfig,
    output_file: str
) -> int:
    """
    Filter Estabelecimentos CSV by CNAE and UF.
    
    Estabelecimentos CSV columns (0-indexed):
    0: CNPJ_BASICO
    1: CNPJ_ORDEM
    2: CNPJ_DV
    5: SITUACAO_CADASTRAL (02 = ATIVA)
    11: CNAE_PRINCIPAL
    20: UF
    21: CEP
    ...
    """
    print(f"🔍 Filtering: {input_file}")
    print(f"   CNAE: {config.cnae_codes}")
    print(f"   UF: {config.uf or 'ALL'}")
    
    count = 0
    matched = 0
    
    with open(input_file, 'r', encoding='latin-1') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.reader(infile, delimiter=';')
        writer = csv.writer(outfile)
        
        # Write header
        writer.writerow([
            'cnpj_basico', 'cnpj_ordem', 'cnpj_dv', 'matriz_filial',
            'nome_fantasia', 'situacao', 'data_situacao', 'motivo_situacao',
            'cidade_exterior', 'pais', 'data_inicio', 'cnae_principal',
            'cnae_secundario', 'tipo_logradouro', 'logradouro', 'numero',
            'complemento', 'bairro', 'cep', 'uf', 'municipio',
            'ddd1', 'telefone1', 'ddd2', 'telefone2', 'ddd_fax', 'fax',
            'email', 'situacao_especial', 'data_situacao_especial'
        ])
        
        for row in reader:
            count += 1
            
            if count % 100000 == 0:
                print(f"   Processed: {count:,} rows, Matched: {matched:,}")
            
            if len(row) < 20:
                continue
            
            # Check CNAE
            cnae = row[11] if len(row) > 11 else ""
            if cnae not in config.cnae_codes:
                continue
            
            # Check situação cadastral (ATIVA = 02)
            situacao = row[5] if len(row) > 5 else ""
            if situacao != config.situacao:
                continue
            
            # Check UF
            if config.uf:
                uf = row[19] if len(row) > 19 else ""
                if uf != config.uf:
                    continue
            
            # Match! Write to output
            writer.writerow(row)
            matched += 1
            
            if config.limit and matched >= config.limit:
                break
    
    print(f"✅ Filtered: {matched:,} records from {count:,} total")
    return matched

def filter_by_segment(
    input_dir: str,
    segment: str,
    uf: Optional[str] = None,
    output_file: str = None,
    limit: int = None
) -> int:
    """
    Filter by predefined segment name.
    
    Example:
        filter_by_segment("./data/receita/", "restaurantes", "SP")
    """
    if segment not in CNAE_SEGMENTS:
        print(f"❌ Unknown segment: {segment}")
        print(f"   Available: {list(CNAE_SEGMENTS.keys())}")
        return 0
    
    cnae_codes = CNAE_SEGMENTS[segment]
    
    input_path = Path(input_dir)
    estab_files = list(input_path.glob("*stabelecimento*.csv")) + \
                  list(input_path.glob("*STABELECIMENTO*.CSV"))
    
    if not estab_files:
        print(f"❌ No Estabelecimentos file found in: {input_dir}")
        return 0
    
    config = FilterConfig(
        cnae_codes=cnae_codes,
        uf=uf,
        limit=limit
    )
    
    output = output_file or f"./data/{segment}_{uf or 'BR'}.csv"
    
    total = 0
    for estab_file in estab_files:
        total += filter_estabelecimentos(str(estab_file), config, output)
    
    return total

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Filter Receita Federal data")
    parser.add_argument("--input", default="./data/receita/", help="Input directory")
    parser.add_argument("--segment", default="restaurantes", help="Business segment")
    parser.add_argument("--uf", help="State code (SP, RJ, etc.)")
    parser.add_argument("--output", help="Output CSV file")
    parser.add_argument("--limit", type=int, help="Max records")
    args = parser.parse_args()
    
    filter_by_segment(
        args.input,
        args.segment,
        args.uf,
        args.output,
        args.limit
    )
