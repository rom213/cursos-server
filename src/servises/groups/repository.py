from flask import  request, jsonify
import requests
from servises.categories.category_model import CategoryModel
from servises.groups.group_model import GroupModel
from servises.Users.user_model import UserModel
from servises.payment.payment_model import PaymentModel
from servises.refer.refer_model import ReferModel
import json
from generateTokenAcces import access_token, generate_token, get_access_token


class GroupRepository:
    def __init__(
        self,
        group_email="",
        member_email="",
        group_description="",
        group_name="",
        role="MEMBER",
        group_id=None,
    ):
        self.group_email = group_email
        self.member_email = member_email
        self.group_description = group_description
        self.group_name = group_name
        self.role = role
        self.group_id= group_id


    def agregar_miembro_grupo_time(self):
        global access_token
        url = f'https://admin.googleapis.com/admin/directory/v1/groups/{self.group_email}/members'
        
        member_data = {
            "email": self.member_email,
            "role": self.role
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=json.dumps(member_data))

        if response.status_code == 401:
            print("Token expirado. Generando nuevo token...")

            access_token = generate_token()  # Se actualiza la variable global
            
            headers['Authorization'] = f'Bearer {access_token}'
            response = requests.post(url, headers=headers, data=json.dumps(member_data))

        if response.status_code in [200, 201]:
            print("Miembro agregado con éxito:")
            self.eliminar_member_minutes()
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None 
    

    def agregar_miembro_grupo(self):
        global access_token  # Se declara la variable global
        url = f'https://admin.googleapis.com/admin/directory/v1/groups/{self.group_email}/members'
        member_data = {
            "email": self.member_email,
            "role": self.role
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=json.dumps(member_data))
        
        if response.status_code == 401:
            print("Token expirado. Generando nuevo token...")
            access_token = generate_token()  # Actualizamos el token global
            headers['Authorization'] = f'Bearer {access_token}'
            response = requests.post(url, headers=headers, data=json.dumps(member_data))

        if response.status_code in [200, 201]:
            print("Miembro agregado con éxito:")
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None 


    def create_member_group_repo(data):
        category = CategoryModel.find(category_id=data["category_id"])
        if not category:
            return (jsonify({"error": f"No existe la categoria"}), 400)
        
        group = GroupModel.get_first_group()

        if group is None:
            return (jsonify({"error": f"No hay grupos disponibles"}), 400)
        
        role = data.get("role", "MEMBER")

        return GroupRepository(
            group_id=group.id,
            group_email=group.group_mail,
            member_email=data["member_email"],
            role=role
        )


    def crear_grupo(self):
        url = 'https://admin.googleapis.com/admin/directory/v1/groups'
        
        group_data = {
            "email": self.group_email,
            "name": self.group_name,
            "description": self.group_description
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(group_data))
        
        if response.status_code in [200, 201]:
            print("Grupo creado con éxito:")
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None

    def eliminar_miembro_grupo(self):
        url = f'https://admin.googleapis.com/admin/directory/v1/groups/{self.group_email}/members/{self.member_email}'
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 204:
            print(f"Miembro {self.member_email} eliminado con éxito del grupo {self.group_email}.")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
        
    def eliminar_member_minutes(self):
            print("vamos a eliminar")
            schedule_data = {
                "group_email": self.group_email,
                "member_email": self.member_email
            }
            # Cambia la URL si el servidor Node.js corre en otra dirección o puerto.
            schedule_response = requests.post("http://localhost:3000/schedule", json=schedule_data)
            return schedule_response.json()

    def process_member_addition(method_name, data):

        ## ALERTA SOLO DEBE EXISTIR EN PAYMENTS SOLO UN GOOGLE_ID CON UNA CATEGORIA, QUEDA PENDIENTE
        repo = GroupRepository.create_member_group_repo(data=data)
        if isinstance(repo, tuple):
            return repo
        
        user = UserModel.get_by_email(email=data["member_email"])

        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        try:
            result = getattr(repo, method_name)()

            payment_status = "SUCCESS" if result else "ERROR"
            is_refer = data.get("google_id_refer") is not None

            print(is_refer)

            payment=PaymentModel.create_payment(
            google_id=user.google_id,
            category_id=data.get("category_id"),
            signature=data.get("reference_code"),
            status=payment_status,
            isRefer=is_refer)

            if is_refer is True:
                refer= ReferModel(google_id=data.get("google_id_refer"), payment_id=payment.id)
                is_valid_refer=refer.verify()

                print(is_valid_refer)
                if not is_valid_refer:
                    return jsonify({"error": "violacion del sistema"}), 423
                
                refer.save()
            
            return jsonify({"message": "the member it was create sastisfactory"}), 200
        except Exception as ex:
            return jsonify({"error": f"Error al agregar el miembro al grupo: {str(ex)}"}), 500
