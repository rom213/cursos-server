from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        with db.engine.begin() as conn:
            print("Modifying verification_codes table...")
            try:
                conn.execute(text("ALTER TABLE verification_codes MODIFY COLUMN email VARCHAR(255) NOT NULL"))
                conn.execute(text("ALTER TABLE verification_codes MODIFY COLUMN code VARCHAR(255) NOT NULL"))
                print("Migration completed successfully.")
            except Exception as e:
                print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
