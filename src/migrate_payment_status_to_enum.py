from app import app, db
from sqlalchemy import text


def migrate():
    with app.app_context():
        with db.engine.connect() as conn:
            conn.execute(
                text(
                    """
                    UPDATE payment
                    SET status = 'ERROR'
                    WHERE status IS NOT NULL
                      AND status NOT IN ('SUCCESS', 'ERROR')
                    """
                )
            )
            conn.execute(
                text(
                    """
                    ALTER TABLE payment
                    MODIFY COLUMN status ENUM('SUCCESS', 'ERROR') NULL
                    """
                )
            )
            conn.commit()
            print("Migration completed successfully: payment.status is now ENUM('SUCCESS','ERROR').")


if __name__ == "__main__":
    migrate()
