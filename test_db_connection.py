import os
import psycopg2
from sqlalchemy import create_engine, text

def test_connection():
    # Load from env or use defaults (be careful regarding exposing creds in logs)
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return

    print(f"🔌 Testing connection to: {db_url.split('@')[1] if '@' in db_url else '***'}")
    
    try:
        engine = create_engine(db_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Connection successful!")
            
            # Check permissions
            try:
                conn.execute(text("CREATE TABLE IF NOT EXISTS connection_test (id serial PRIMARY KEY)"))
                conn.execute(text("DROP TABLE connection_test"))
                print("✅ Write permissions valid")
            except Exception as e:
                print(f"❌ Write permission error: {e}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
