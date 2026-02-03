from app.database import SessionLocal
from app.schema import LogScraping, Empresa

def check_specific():
    db = SessionLocal()
    try:
        print(f"🔌 Checking Specific Logs...")
        logs = db.query(LogScraping).filter(LogScraping.termo_busca == "Agência Marketing Av Paulista").all()
        for log in logs:
            print(f"[{log.status_extracao}] {log.termo_busca} ({log.data_hora})")
            
        print("\n📂 Checking Companies:")
        companies = db.query(Empresa).filter(Empresa.razao_social.ilike("%Agência%")).all()
        for c in companies:
            print(f"- {c.razao_social} | {c.site_url}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_specific()
