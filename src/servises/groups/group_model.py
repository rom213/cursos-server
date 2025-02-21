from models.Group import Group
from models import db

class GroupModel(Group):
    
    @staticmethod
    def create_group(name, group_mail, description, count_members, category_id):
        new_group = Group(
            name=name,
            group_mail=group_mail,
            description=description,
            count_members=count_members,
            category_id=category_id
        )
        db.session.add(new_group)
        db.session.commit()
        return new_group
    
    @staticmethod
    def get_group_by_id(group_id):
        return Group.query.get(group_id)
    
    @staticmethod
    def get_first_group():
        groups= Group.query.filter(Group.count_members <= 550).first()
        return groups if groups else None
    
    @staticmethod
    def update_group(group_id, **kwargs):
        group = Group.query.get(group_id)
        if group:
            for key, value in kwargs.items():
                if hasattr(group, key):
                    setattr(group, key, value)
            db.session.commit()
            return group
        return None
    
    @staticmethod
    def delete_group(group_id):
        group = Group.query.get(group_id)
        if group:
            db.session.delete(group)
            db.session.commit()
            return True
        return False

