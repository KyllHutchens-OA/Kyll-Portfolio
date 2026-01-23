"""Run migration V3: Change round column to VARCHAR."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.data.database import engine

print("Running migration V3: Changing round column from INTEGER to VARCHAR(50)...")

migration_sql = text("""
ALTER TABLE matches
ALTER COLUMN round TYPE VARCHAR(50);
""")

try:
    with engine.connect() as connection:
        connection.execute(migration_sql)
        connection.commit()
    print("✅ Migration V3 completed successfully!")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
