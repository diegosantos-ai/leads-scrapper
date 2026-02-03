"""
Database Reset Tool
Drops and recreates all tables to fix schema mismatches.
"""
import sys
from app.database import engine, Base
from app.schema import Empresa, Contato, LogScraping

def reset_db():
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("FORCING DATABASE RESET...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ Database reset complete!")
    else:
        print("Run with --force to confirm reset.")

if __name__ == "__main__":
    reset_db()
