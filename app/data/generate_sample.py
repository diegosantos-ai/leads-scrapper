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
            
            # Create Empresa
            empresa = Empresa(
                cnpj=cnpj,
                razao_social=data.get('nome'),
                nome_fantasia=data.get('fantasia'),
                setor_cnae=client.extract_atividade(data),
                porte=data.get('porte'),
                natureza_juridica=data.get('natureza_juridica'),
                data_abertura=data.get('abertura'),
                situacao_cadastral=data.get('situacao'),
                capital_social=data.get('capital_social'),
                telefone_empresa=data.get('telefone'),
                email_empresa=data.get('email'),
                cidade=data.get('municipio'),
                estado=data.get('uf'),
                endereco_completo=f"{data.get('logradouro', '')}, {data.get('numero', '')}, {data.get('bairro', '')}",
                segmento_mercado=segment
            )
            
            db.add(empresa)
            db.flush()
            
            # Add socios
            for socio_data in data.get('qsa', []):
                socio = Socio(
                    empresa_id=empresa.empresa_id,
                    nome_completo=socio_data.get('nome'),
                    cargo=socio_data.get('qual')
                )
                db.add(socio)
            
            db.commit()
            count += 1
            print(f"   ✅ Added: {data.get('nome', 'N/A')[:50]}")
            print(f"      Sócios: {len(data.get('qsa', []))}")
        
        print(f"\n🎉 Done! Added {count} companies to '{segment}'")
        return count
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(generate_sample_dataset())
