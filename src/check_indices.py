from app import app, db
from sqlalchemy import text

def check_indices():
    with app.app_context():
        with db.engine.connect() as conn:
            result = conn.execute(text("SHOW INDEX FROM refer"))
            indices = result.fetchall()
            print("Current indices:")
            for index in indices:
                print(index)
                # Check if refund_id is unique
                if index[4] == 'refund_id':
                    print(f"refund_id index non_unique: {index[1]}")

if __name__ == "__main__":
    check_indices()
