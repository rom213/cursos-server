from models import db

class TiendaCourse(db.Model):
    __tablename__ = 'tienda_course'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255))
    autor = db.Column(db.String(255))
    url_curso = db.Column(db.String(500))
    pack_id = db.Column(db.String(100))
    pack_nombre = db.Column(db.String(255))
    pack_cantidad_cursos = db.Column(db.Integer)
    pilar_id = db.Column(db.String(100))
    keywords = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'autor': self.autor,
            'url_curso': self.url_curso,
            'pack_id': self.pack_id,
            'pack_nombre': self.pack_nombre,
            'pack_cantidad_cursos': self.pack_cantidad_cursos,
            'pilar_id': self.pilar_id,
            'keywords': self.keywords
        }
