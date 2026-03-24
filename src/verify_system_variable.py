from app import app, db
from models.SystemVariable import SystemVariable

def verify():
    with app.app_context():
        var = SystemVariable.query.filter_by(campo_codigo="CAMBIO_DOLAR").first()
        if var:
            print(f"Verified Variable: {var.campo_codigo}")
            print(f"Value: {var.dato}")
            print(f"Description: {var.descripcion}")
        else:
            print("Variable not found!")

if __name__ == "__main__":
    verify()
