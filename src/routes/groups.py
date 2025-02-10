from flask import Blueprint, request, jsonify
import requests
import json

group_bp = Blueprint("groups", __name__)

class GroupRepository:
    def __init__(
        self,
        group_email="",
        member_email="",
        group_description="",
        group_name="",
        role="MEMBER",
        access_token="ya29.c.c0ASRK0GboqnpDU56jKY4tJfj7rKpPyJtw8cQqbjmXbtnSCW_aA5yvKGoSM-gWsDVrGvnr0dkb_zN9vgSskCXOvqjHXFGFyqzgmEUaBp0p8NNajpd1B3Upkg2P3uCZ7krO-75_H9fOfjgvtgrEwyh1B1Y-ZI650T3uf62OT2-7_qhslCirvkjFHNSd11lgA5rs6P5tqerYP7hrtMngzS6ogqEroPAPnV3_vW9mzZJiGIEAAc6HKYnqNvLnZGdqC7pJrMH1yY4D9p5MplIW_vOVMxP52r26SizCEwchXlj6NQUK8K9m0XdQbCEW0piEfXAZwvM0f0qusdPTBxeXHEgy7faBQwEDEMd9qvQ03qVL6U0CMW00nGkfML1lH385K1n_yuzB7eFShMU65h5dWMc8gIZuuiI8ughcWJWOh-vM8ve77OJWQS4XiQ73M6FjvoWqUVYkRQXqSbwybp-om8rS81USpcd7nYnM0zW16ehiunFtIg0BjXOs6orkRr8VhuWQrnrw2uanlU1jxZQnnSMtoe9ZVzxJzqS2Y1c--rxarvyYJSu5ukchx26db6a5tzUwrnw26Qsfrh3curFSRRmxpaoop3ZWu4f9dR34j9eXtkXebuFhyuhz1vyhrW0qBvq98Zc26lRoVs2WlieSmxRlvtX9fY73Yhsx71pao73h-l5tJ4SgrtRoObqRm5lcw56w8yBhxnV0OJp52g-j7zX883QaU7a0X5-tlbaplvy7g2zz8B1abvZjkcc18tqc9JvrMnm2tRMlfhMMXi0Ry0_6prRI1vbnoiZbFdF1Uj1hX5yggl0rvWWwQxcza2yxvivU92yZ0zcjj2co2q7tdlXspw_g92rsfkRtyQqFfOw3VddIM7kOIrBRSqYJqOOligZXy7jRV4wi8X-SIM_Qv3WeY26lh73nl_XsdR0Fsoa5Wful3gVgxgur0F3X1qleSR7mZ_1eW9dYq4ijIfQFYu_O6kaZ9mbBJZrpZIae8xlb3hYIxk9hRwjaQ1g"
    ):
        self.access_token = access_token
        self.group_email = group_email
        self.member_email = member_email
        self.group_description = group_description
        self.group_name = group_name
        self.role = role

    def agregar_miembro_grupo(self):
        url = f'https://admin.googleapis.com/admin/directory/v1/groups/{self.group_email}/members'
        
        member_data = {
            "email": self.member_email,
            "role": self.role
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(member_data))
        
        if response.status_code in [200, 201]:
            print("Miembro agregado con éxito:")
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None

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

# -----------------------
# Endpoints del Blueprint
# -----------------------

@group_bp.route("/create-group", methods=["POST"])
def create_group():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se proporcionaron datos"}), 400

    # Validar que se reciban los parámetros necesarios
    required_fields = ["group_email", "group_name", "group_description"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Falta el parámetro: {field}"}), 400

    group_email = data["group_email"]
    group_name = data["group_name"]
    group_description = data["group_description"]

    # Crear la instancia de la clase y ejecutar la creación del grupo
    group_repo = GroupRepository(
        group_email=group_email,
        group_name=group_name,
        group_description=group_description
    )
    result = group_repo.crear_grupo()
    if result:
        return jsonify(result), 201
    else:
        return jsonify({"error": "Error al crear el grupo"}), 400


@group_bp.route("/add-member", methods=["POST"])
def add_member():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se proporcionaron datos"}), 400

    # Validar que se reciban los parámetros necesarios
    required_fields = ["group_email", "member_email"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Falta el parámetro: {field}"}), 400

    group_email = data["group_email"]
    member_email = data["member_email"]
    role = data.get("role", "MEMBER")  # Si no se envía el rol, se usa "MEMBER" por defecto

    # Crear la instancia de la clase y agregar el miembro al grupo
    group_repo = GroupRepository(
        group_email=group_email,
        member_email=member_email,
        role=role
    )
    result = group_repo.agregar_miembro_grupo()
    if result:
        return jsonify(result), 201
    else:
        return jsonify({"error": "Error al agregar el miembro al grupo"}), 400


@group_bp.route("/remove-member", methods=["DELETE"])
def remove_member():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se proporcionaron datos"}), 400

    # Validar que se reciban los parámetros necesarios
    required_fields = ["group_email", "member_email"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Falta el parámetro: {field}"}), 400

    group_email = data["group_email"]
    member_email = data["member_email"]

    # Crear la instancia de la clase y eliminar el miembro del grupo
    group_repo = GroupRepository(
        group_email=group_email,
        member_email=member_email
    )
    result = group_repo.eliminar_miembro_grupo()
    if result:
        return jsonify({"message": f"Miembro {member_email} eliminado del grupo {group_email}"}), 200
    else:
        return jsonify({"error": "Error al eliminar el miembro del grupo"}), 400
