from models.Category import Category
from models import db  # Asegúrate de importar la instancia de la base de datos

class CategoryModel(Category):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Llama al constructor de la clase padre

    @staticmethod
    def create(data):
        try:
            new_category = CategoryModel(**data)
            db.session.add(new_category)
            db.session.commit()
            return new_category
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear la categoría: {e}")
            return None

    @staticmethod
    def eliminar(category_id):
        category = CategoryModel.query.get(category_id)
        if category:
            db.session.delete(category)
            db.session.commit()
            return True
        return False

    @staticmethod
    def update(category_id, data):
        category = CategoryModel.query.get(category_id)
        if category:
            for key, value in data.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            db.session.commit()
            return category
        return None

    @staticmethod
    def find(category_id):
        return CategoryModel.query.get(category_id)
