from app.database import SessionLocal, engine
from app.schema import Empresa, Contato, LogScraping
from sqlalchemy import text

def check_data():
    db = SessionLocal()
    try:
        print(f"🔌 Checking Database...")
        
        # Count Total
        count_emp = db.query(Empresa).count()
        print(f"\n📊 TOTAL DE LEADS NO BANCO: {count_emp}")
        
        # Count by Segment
        print("\n📂 Por Segmento:")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT segmento_mercado, COUNT(*) FROM empresas GROUP BY segmento_mercado"))
            for row in result:
                print(f"   - {row[0]}: {row[1]} empresas")
        
        # List Recent
        print(f"\n🕒 Últimas 5 empresas adicionadas:")
        recents = db.query(Empresa).order_by(Empresa.empresa_id.desc()).limit(5).all()
        for r in recents:
            print(f"   - {r.razao_social} ({r.segmento_mercado})")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
