from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        with db.engine.connect() as conn:
            # 1. Find Foreign Key Name
            # Query information_schema to find the FK name for refer.refund_id
            # query = text("""
            #     SELECT CONSTRAINT_NAME 
            #     FROM information_schema.KEY_COLUMN_USAGE 
            #     WHERE TABLE_NAME = 'refer' 
            #     AND COLUMN_NAME = 'refund_id' 
            #     AND REFERENCED_TABLE_NAME = 'refund'
            #     AND TABLE_SCHEMA = DATABASE()
            # """)
            # result = conn.execute(query)
            # fk_name = result.scalar()
            
            # if fk_name:
            #     print(f"Found Foreign Key: {fk_name}")
                
            #     # 2. Drop Foreign Key
            #     print(f"Dropping Foreign Key: {fk_name}")
            #     conn.execute(text(f"ALTER TABLE refer DROP FOREIGN KEY {fk_name}"))
                
            #     # 3. Drop Unique Index
            #     # We know the index name is likely 'refund_id' or same as FK name, but let's check indices again to be sure or just try dropping 'refund_id'
            #     # Inspect indices again to be safe
            #     res_idx = conn.execute(text("SHOW INDEX FROM refer"))
            #     indices = res_idx.fetchall()
            #     index_to_drop = None
            #     for idx in indices:
            #         # idx[2] is Key_name, idx[4] is Column_name, idx[1] is Non_unique
            #         if idx[4] == 'refund_id' and idx[1] == 0:
            #             index_to_drop = idx[2]
            #             break
                
            #     if index_to_drop:
            #         print(f"Dropping Unique Index: {index_to_drop}")
            #         conn.execute(text(f"ALTER TABLE refer DROP INDEX {index_to_drop}"))
            #     else:
            #         print("Unique index not found (maybe already dropped or named differently).")

            #     # 4. Add Normal Index
            #     print("Adding non-unique index on refund_id")
            #     # Check if index exists first? If we dropped it, it doesn't.
            #     conn.execute(text("ALTER TABLE refer ADD INDEX refund_id (refund_id)"))

            #     # 5. Re-add Foreign Key
            #     print(f"Re-adding Foreign Key: {fk_name}")
            #     conn.execute(text(f"ALTER TABLE refer ADD CONSTRAINT {fk_name} FOREIGN KEY (refund_id) REFERENCES refund(id)"))
            conn.execute(text("ALTER TABLE refund ADD number_acc_res VARCHAR(255)"))
            conn.commit()
            print("Migration completed successfully.")


if __name__ == "__main__":
    migrate()
