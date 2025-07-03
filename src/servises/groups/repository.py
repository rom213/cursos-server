from flask import  request, jsonify
import requests
from servises.categories.category_model import CategoryModel
from servises.groups.group_model import GroupModel
from servises.Users.user_model import UserModel
from servises.payment.payment_model import PaymentModel
from servises.refer.refer_model import ReferModel
import json
from generateTokenAcces import access_token, generate_token, get_access_token
import os



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
        try:
            repo, google_id, google_id_refer = GroupService.add_member(method_name, data)

            user = UserService.get_user_by_google_id(google_id)
            repo.member_email = user.email

            refer = ReferService.handle_referral(data)
            is_refer = refer is not None

            payment = PaymentService.process_payment(user.google_id, data, is_refer)

            result = getattr(repo, method_name)()
            payment.status = "SUCCESS" if result else "ERROR"
            payment.save()

            if refer:
                refer.payment_id = payment.id
                refer.save()

            return jsonify({"message": "El miembro fue creado satisfactoriamente"}), 200

        except ValueError as ve:
            return jsonify({"error": str(ve)}), 404
        except PermissionError as pe:
            return jsonify({"error": str(pe)}), 423
        except Exception as ex:
            return jsonify({"error": f"Error al agregar el miembro al grupo: {str(ex)}"}), 500




class GroupService:
    @staticmethod
    def add_member(method_name: str, data: dict):
        repo = GroupRepository.create_member_group_repo(data=data)
        if isinstance(repo, tuple):
            return repo, None, None

        return repo, data.get("google_id"), data.get("google_id_refer")
    

class UserService:
    @staticmethod
    def get_user_by_google_id(google_id: str):
        user = UserModel.get_by_google_id(google_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        return user

class ReferService:
    @staticmethod
    def handle_referral(data: dict):
        google_id_refer = data.get("google_id_refer")
        if not google_id_refer:
            return None

        refund_percentage = float(os.getenv("REFUND_PERCENTAGE"))
        pay_value = float(data.get("pay_value_refer", "0"))
        refund_value = (pay_value * refund_percentage) / 100

        refer = ReferModel(google_id=google_id_refer, value=refund_value)
        if not refer.verify():
            raise PermissionError("Referido no válido")

        return refer
    
class PaymentService:
    @staticmethod
    def process_payment(user_google_id, data, is_refer):
        cat = CategoryModel.get_by_id(data.get("category_id"))

        # lo usamos para atrapar errores y evitar el no registro de una compra
        try:
            if is_refer:
                cat.calc_price(False, False)
            else:
                is_first_bought = not  UserModel.is_bought(google_id=data.get("google_id"))
                # print(is_first_bought)
                cat.calc_price(is_first_bought, False)
        except Exception as e:
            print(e)
        
        
        payment = PaymentModel(
            status="ERROR",
            price=cat.descuento_total_price,
            is_refer=is_refer,
            category_id=data.get("category_id"),
            signature=data.get("reference_code"),
            google_id=user_google_id
        )

        if not payment.verify():
            raise PermissionError("Pago no verificado")

        return payment
