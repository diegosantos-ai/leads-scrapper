"""Debug: Find exact missing columns"""
from app.database import engine
from app.schema import Empresa
from sqlalchemy import inspect

inspector = inspect(engine)
db_cols = {c['name'] for c in inspector.get_columns('empresas')}
model_cols = {c.name for c in Empresa.__table__.columns}

print("Missing in DB (need ALTER TABLE):")
for col in sorted(model_cols - db_cols):
    print(f"  ALTER TABLE empresas ADD COLUMN IF NOT EXISTS {col} VARCHAR(255);")

print("\nIn DB but not in Model:")
for col in sorted(db_cols - model_cols):
    print(f"  {col}")
