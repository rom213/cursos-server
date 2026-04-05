import logging
import requests
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

from servises.categories.category_model import CategoryModel
from servises.groups.admin_directory_client import ejecutar_con_reintento_401
from servises.Users.user_model import UserModel
from servises.payment.payment_model import PaymentModel
from models.Payment import PaymentStatus
from models.Group import Group
from servises.refer.refer_model import ReferModel
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
        try:
            def _insert(s):
                return (
                    s.members()
                    .insert(
                        groupKey=self.group_email,
                        body={"email": self.member_email, "role": self.role},
                    )
                    .execute()
                )

            result = ejecutar_con_reintento_401(_insert)
            logger.info("Miembro agregado con éxito (time): %s", self.member_email)
            self.eliminar_member_minutes()
            return result
        except HttpError as e:
            if getattr(e.resp, "status", None) == 409:
                logger.info(
                    "Usuario %s ya es miembro del grupo (409). Se considera éxito.",
                    self.member_email,
                )
                return {"status": "already_member"}
            raw = getattr(e, "content", b"").decode(errors="replace")
            logger.error("Error Google API [%s]: %s | %s", e.resp.status if e.resp else "?", e.reason, raw)
            return None

    def agregar_miembro_grupo(self):
        try:
            def _insert(s):
                return (
                    s.members()
                    .insert(
                        groupKey=self.group_email,
                        body={"email": self.member_email, "role": self.role},
                    )
                    .execute()
                )

            result = ejecutar_con_reintento_401(_insert)
            logger.info("Miembro agregado con éxito: %s -> %s | resp: %s", self.member_email, self.group_email, result)
            return result
        except HttpError as e:
            if getattr(e.resp, "status", None) == 409:
                logger.info(
                    "Usuario %s ya es miembro del grupo (409). Se considera éxito.",
                    self.member_email,
                )
                return {"status": "already_member"}
            raw = getattr(e, "content", b"").decode(errors="replace")
            logger.error("Error Google API [%s]: %s | %s", e.resp.status if e.resp else "?", e.reason, raw)
            return None


    def create_member_group_repo(data):
        category = CategoryModel.find(category_id=data["category_id"])
        if not category:
            raise ValueError("No existe la categoria")

        # Grupo de Google asociado a la categoría comprada (no el "primer" grupo genérico)
        group = Group.query.filter_by(category_id=category.id).first()

        if group is None:
            raise ValueError("No hay grupo configurado para esta categoría en la base de datos")
        
        role = data.get("role", "MEMBER")

        return GroupRepository(
            group_id=group.id,
            group_email=group.group_mail,
            role=role
        )


    def crear_grupo(self):
        body = {
            "email": self.group_email,
            "name": self.group_name,
        }
        if self.group_description is not None:
            body["description"] = self.group_description

        try:
            def _create(s):
                return s.groups().insert(body=body).execute()

            result = ejecutar_con_reintento_401(_create)
            logger.info("Grupo creado con éxito: %s", self.group_email)
            return result
        except HttpError as e:
            raw = getattr(e, "content", b"").decode(errors="replace")
            logger.error("Error Google API [%s]: %s | %s", e.resp.status if e.resp else "?", e.reason, raw)
            return None

    def eliminar_miembro_grupo(self):
        try:
            def _delete(s):
                s.members().delete(
                    groupKey=self.group_email, memberKey=self.member_email
                ).execute()
                return True

            ejecutar_con_reintento_401(_delete)
            logger.info("Miembro %s eliminado del grupo %s.", self.member_email, self.group_email)
            return True
        except HttpError as e:
            raw = getattr(e, "content", b"").decode(errors="replace")
            logger.error("Error Google API [%s]: %s | %s", e.resp.status if e.resp else "?", e.reason, raw)
            return False
        
    def eliminar_member_minutes(self):
            logger.info("Programando eliminación temporal: %s del grupo %s", self.member_email, self.group_email)
            schedule_data = {
                "group_email": self.group_email,
                "member_email": self.member_email
            }
            # Cambia la URL si el servidor Node.js corre en otra dirección o puerto.
            schedule_response = requests.post("http://localhost:3000/schedule", json=schedule_data)
            return schedule_response.json()

    @staticmethod
    def process_member_addition(method_name, data):
        payment = None
        try:
            repo, google_id, google_id_refer = GroupService.add_member(method_name, data)

            
            user = UserService.get_user_by_google_id(google_id)
            
            repo.member_email = user.email
            refer = ReferService.handle_referral(data)

            is_refer = refer is not None

            # Procesamos el pago y LO GUARDAMOS DE UNA VEZ (como pending o success luego)
            payment = PaymentService.process_payment(user.google_id, data, is_refer)
            # Podríamos guardar aquí si PaymentService.process_payment no guarda automáticamente (parece que no guarda, solo crea instancia)
            # payment.save() # Si el modelo lo requiere para tener ID

            result = getattr(repo, method_name)()

            payment.status = PaymentStatus.SUCCESS if result else PaymentStatus.ERROR
            payment.save()

            if refer:
                refer.payment_id = payment.id
                refer.save()

            return {"status": "success", "message": "El miembro fue creado satisfactoriamente"}

        except ValueError as ve:
            if payment:
                payment.status = PaymentStatus.ERROR
                payment.save()
            else:
                PaymentService.save_error_payment(data)
            return {"status": "error", "error": str(ve)}

        except PermissionError as pe:
            if payment:
                payment.status = PaymentStatus.ERROR
                payment.save()
            else:
                PaymentService.save_error_payment(data)
            return {"status": "error", "error": str(pe)}

        except Exception as ex:
            logger.error("Error inesperado en process_member_addition: %s", ex, exc_info=True)
            if payment:
                payment.status = PaymentStatus.ERROR
                payment.save()
            else:
                PaymentService.save_error_payment(data)
            return {"status": "error", "error": f"Error al agregar el miembro al grupo: {str(ex)}"}

    @staticmethod
    def process_member_addition_time(data):
        try:
            repo, google_id, _ = GroupService.add_member("agregar_miembro_grupo_time", data)
            
            
            
            user = UserService.get_user_by_google_id(google_id)
            UserModel.no_mas_vista_previa_drive(google_id)
            repo.member_email = user.email
            result = repo.agregar_miembro_grupo_time()
            if result:
                return {"status": "success", "message": "El miembro fue creado satisfactoriamente"}
            return {"status": "error", "error": "No se pudo agregar el miembro al grupo"}
        except ValueError as ve:
            return {"status": "error", "error": str(ve)}
        except PermissionError as pe:
            return {"status": "error", "error": str(pe)}
        except Exception as ex:
            logger.error("Error inesperado en process_member_addition_time: %s", ex, exc_info=True)
            return {"status": "error", "error": f"Error al agregar el miembro al grupo: {str(ex)}"}




class GroupService:
    @staticmethod
    def add_member(method_name: str, data: dict):
        repo = GroupRepository.create_member_group_repo(data=data)
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
        pay_value = float(data.get("pay_val", "0"))
        refund_value = (pay_value * refund_percentage) / 100
        refer = ReferModel(google_id=google_id_refer, value=refund_value, porcentage=refund_percentage)
        if not refer.verify():
            raise PermissionError("Referido no válido")

        return refer
    
class PaymentService:
    @staticmethod
    def process_payment(user_google_id, data, is_refer):
        
        cat = CategoryModel.get_by_id(data.get("category_id"))

        # Misma firma que en routes.payments: calc_price(descuento=...); sin descuento extra = 0
        values = {"precio_final": 0, "descuento_aplicado": 0}
        if cat:
            try:
                values = cat.calc_price(descuento=0)
            except Exception as e:
                logger.error("Error calculando precio: %s", e)
        # work
        payment = PaymentModel(
            status=PaymentStatus.ERROR,
            price=data.get("pay_val"),
            is_refer=is_refer,
            category_id=data.get("category_id"),
            signature=data.get("reference_code"),
            google_id=user_google_id
        )
        if not payment.verify():
            raise PermissionError("Pago no verificado")
        return payment

    @staticmethod
    def save_error_payment(data):
        try:
             # Intentamos obtener un precio aproximado o 0
            price = 0
            try:
                cat = CategoryModel.get_by_id(data.get("category_id"))
                if cat:
                    values = cat.calc_price(descuento=0)
                    price = values.get("precio_final", 0)
            except:
                pass

            payment = PaymentModel(
                status=PaymentStatus.ERROR,
                price=price,
                is_refer=False,
                category_id=data.get("category_id"),
                signature=data.get("reference_code"),
                google_id=data.get("google_id"),
                info_error=data
            )
            payment.save()
            logger.info("Pago con error guardado exitosamente")
            return payment
        except Exception as e:
            logger.error("Error crítico al guardar pago fallido: %s", e)
            return None
