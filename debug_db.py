from app.database import SessionLocal
from app.schema import Empresa

def check_completeness():
    db = SessionLocal()
    try:
        print(f"🔌 Checking Data Completeness (QuickWinTest)...")
        companies = db.query(Empresa).filter(Empresa.segmento_mercado == "QuickWinTest").all()
        
        for c in companies:
            print(f"\n📊 {c.razao_social}")
            print(f"   Nome Fantasia: {c.nome_fantasia}")
            print(f"   CNPJ: {c.cnpj}")
            print(f"   Cidade: {c.cidade} | Estado: {c.estado}")
            print(f"   Setor CNAE: {c.setor_cnae}")
            print(f"   Faturamento: {c.faturamento_estimado}")
            print(f"   Colaboradores: {c.tamanho_colaboradores}")
            print(f"   Site: {c.site_url}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_completeness()
