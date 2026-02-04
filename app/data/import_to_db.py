"""
Database Importer - Import filtered CNPJ data into PostgreSQL

Reads the filtered CSV and creates Empresa + Contato records.

Usage:
    python -m app.data.import_to_db --input filtered.csv --segment "Restaurantes SP"
"""

import csv
from pathlib import Path
from typing import Optional
from app.database import SessionLocal
from app.schema import Empresa, Contato

def format_cnpj(basico: str, ordem: str, dv: str) -> str:
    """Format CNPJ from parts to standard format."""
    cnpj = f"{basico.zfill(8)}{ordem.zfill(4)}{dv.zfill(2)}"
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"

def format_telefone(ddd: str, numero: str) -> Optional[str]:
    """Format phone number."""
    if not ddd or not numero:
        return None
    return f"({ddd}) {numero[:4]}-{numero[4:]}" if len(numero) >= 8 else f"({ddd}) {numero}"

def import_csv_to_db(
    input_file: str,
    segment: str,
    batch_size: int = 500,
    limit: Optional[int] = None
) -> int:
    """
    Import filtered CSV to database.
    
    CSV expected columns (from filter_cnae output):
    0: cnpj_basico, 1: cnpj_ordem, 2: cnpj_dv, 3: matriz_filial,
    4: nome_fantasia, 5: situacao, ..., 11: cnae_principal,
    14: logradouro, 15: numero, 17: bairro, 18: cep, 19: uf, 20: municipio,
    21: ddd1, 22: telefone1, 27: email
    """
    print(f"📥 Importing: {input_file}")
    print(f"   Segment: {segment}")
    
    db = SessionLocal()
    count = 0
    imported = 0
    skipped = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            batch = []
            
            for row in reader:
                count += 1
                
                if limit and count > limit:
                    break
                
                # Build CNPJ
                cnpj = format_cnpj(
                    row.get('cnpj_basico', ''),
                    row.get('cnpj_ordem', ''),
                    row.get('cnpj_dv', '')
                )
                
                # Check if already exists
                existing = db.query(Empresa).filter(Empresa.cnpj == cnpj).first()
                if existing:
                    skipped += 1
                    continue
                
                # Build address
                endereco_parts = [
                    row.get('tipo_logradouro', ''),
                    row.get('logradouro', ''),
                    row.get('numero', ''),
                    row.get('bairro', ''),
                ]
                endereco = " ".join([p for p in endereco_parts if p])
                
                # Create Empresa
                empresa = Empresa(
                    cnpj=cnpj,
                    razao_social=row.get('nome_fantasia') or f"CNPJ {cnpj}",
                    nome_fantasia=row.get('nome_fantasia'),
                    setor_cnae=row.get('cnae_principal'),
                    cidade=row.get('municipio'),
                    estado=row.get('uf'),
                    endereco_completo=endereco,
                    telefone_empresa=format_telefone(
                        row.get('ddd1', ''),
                        row.get('telefone1', '')
                    ),
                    email_empresa=row.get('email', '').lower() if row.get('email') else None,
                    segmento_mercado=segment,
                    situacao_cadastral="ATIVA"
                )
                
                batch.append(empresa)
                
                if len(batch) >= batch_size:
                    db.add_all(batch)
                    db.commit()
                    imported += len(batch)
                    print(f"   Imported: {imported:,} (Skipped: {skipped:,})")
                    batch = []
            
            # Final batch
            if batch:
                db.add_all(batch)
                db.commit()
                imported += len(batch)
        
        print(f"✅ Import complete!")
        print(f"   Total rows: {count:,}")
        print(f"   Imported: {imported:,}")
        print(f"   Skipped (duplicates): {skipped:,}")
        
        return imported
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Import CNPJ data to database")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--segment", required=True, help="Market segment name")
    parser.add_argument("--batch", type=int, default=500, help="Batch size")
    parser.add_argument("--limit", type=int, help="Max records to import")
    args = parser.parse_args()
    
    import_csv_to_db(args.input, args.segment, args.batch, args.limit)
