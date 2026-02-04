"""
Generate Sample Dataset - Use ReceitaWS to create a sample restaurant dataset

Since the bulk download is timing out, we'll use ReceitaWS API to fetch
sample records for testing the pipeline.
"""

import asyncio
from app.scrapers.receita_ws import ReceitaWSClient
from app.database import SessionLocal
from app.schema import Empresa, Socio

# Sample CNPJs of known restaurant chains in SP
SAMPLE_CNPJS = [
    "61412110000155",  # McDonald's Brasil
    "07526557000100",  # Habib's
    "60811916000133",  # Outback
    "03766873000106",  # Madero
    "14380200000121",  # Coco Bambu
    "47960950000121",  # Magazine Luiza (bonus - retail)
]

async def generate_sample_dataset(segment: str = "Restaurantes SP", limit: int = 5):
    """Fetch sample data from ReceitaWS and save to DB."""
    
    client = ReceitaWSClient()
    db = SessionLocal()
    
    try:
        print(f"🍕 Generating sample dataset: {segment}")
        print(f"   Using {len(SAMPLE_CNPJS)} sample CNPJs\n")
        
        count = 0
        for cnpj in SAMPLE_CNPJS[:limit]:
            data = await client.fetch(cnpj)
            
            if not data or data.get('status') == 'ERROR':
                continue
            
            # Check if exists
            existing = db.query(Empresa).filter(Empresa.cnpj == cnpj).first()
            if existing:
                print(f"   ⏩ Already exists: {data.get('nome', 'N/A')[:40]}")
                continue
            
            # Truncate values to avoid DB errors
            telefone = data.get('telefone', '')[:20] if data.get('telefone') else None
            email = data.get('email', '')[:255].lower() if data.get('email') else None
            endereco = f"{data.get('logradouro', '')}, {data.get('numero', '')}, {data.get('bairro', '')}"
            
            # Create Empresa
            empresa = Empresa(
                cnpj=cnpj,
                razao_social=data.get('nome', '')[:255],
                nome_fantasia=data.get('fantasia', '')[:255] if data.get('fantasia') else None,
                setor_cnae=client.extract_atividade(data)[:255] if client.extract_atividade(data) else None,
                porte=data.get('porte', '')[:100] if data.get('porte') else None,
                natureza_juridica=data.get('natureza_juridica', '')[:255] if data.get('natureza_juridica') else None,
                data_abertura=data.get('abertura', '')[:10] if data.get('abertura') else None,
                situacao_cadastral=data.get('situacao', '')[:50] if data.get('situacao') else None,
                capital_social=str(data.get('capital_social', ''))[:50] if data.get('capital_social') else None,
                telefone_empresa=telefone,
                email_empresa=email,
                cidade=data.get('municipio', '')[:100] if data.get('municipio') else None,
                estado=data.get('uf', '')[:2] if data.get('uf') else None,
                endereco_completo=endereco,
                segmento_mercado=segment
            )
            
            db.add(empresa)
            db.flush()
            
            # Add socios
            for socio_data in data.get('qsa', []):
                socio = Socio(
                    empresa_id=empresa.empresa_id,
                    nome_completo=socio_data.get('nome', '')[:255],
                    cargo=socio_data.get('qual', '')[:150] if socio_data.get('qual') else None
                )
                db.add(socio)
            
            db.commit()
            count += 1
            print(f"   ✅ Added: {data.get('nome', 'N/A')[:50]}")
            print(f"      Sócios: {len(data.get('qsa', []))}")
        
        print(f"\n🎉 Done! Added {count} companies to '{segment}'")
        return count
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(generate_sample_dataset())
