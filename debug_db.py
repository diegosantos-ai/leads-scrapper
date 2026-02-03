from app.database import SessionLocal, engine
from app.schema import Empresa, Contato, LogScraping
from sqlalchemy import text

def check_data():
    db = SessionLocal()
    try:
        print(f"🔌 Connected to: {engine.url}")
        
        # Check Tables
        print("\n📊 Checking Tables:")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
            tables = [row[0] for row in result]
            print(f"   Found tables: {tables}")

        # Check Empresas
        count_emp = db.query(Empresa).count()
        print(f"\n🏢 Empresas: {count_emp}")
        users = db.query(Empresa).all()
        for u in users:
            print(f"   - {u.razao_social} (ID: {u.empresa_id})")

        # Check Logs
        count_logs = db.query(LogScraping).count()
        print(f"\n📜 Logs: {count_logs}")
        logs = db.query(LogScraping).all()
        for l in logs:
            print(f"   - {l.status_extracao} ({l.data_hora})")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
