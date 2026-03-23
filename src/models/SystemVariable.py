from . import db

class SystemVariable(db.Model):
    __tablename__ = 'system_variables'

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(255), nullable=True)
    dato = db.Column(db.String(255), nullable=False)
    observacion = db.Column(db.Text, nullable=True)
    tabla = db.Column(db.String(100), nullable=True)
    campo_codigo = db.Column(db.String(100), unique=True, nullable=False)

    def __init__(self, campo_codigo, dato, descripcion=None, observacion=None, tabla=None):
        self.campo_codigo = campo_codigo
        self.dato = dato
        self.descripcion = descripcion
        self.observacion = observacion
        self.tabla = tabla

    def to_dict(self):
        return {
            "id": self.id,
            "campo_codigo": self.campo_codigo,
            "dato": self.dato,
            "descripcion": self.descripcion,
            "observacion": self.observacion,
            "tabla": self.tabla
        }
