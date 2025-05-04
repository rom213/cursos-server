from flask import Blueprint, request, jsonify, session
from models.account import AccountType
from servises.account.account_repository import AccountRepository
from servises.Users.user_model import UserModel


account_bp = Blueprint("account", __name__)


@account_bp.route("/update", methods=["POST"])
def update():
    try:
        data = request.get_json()
        
        cuentas = ['nequi', 'daviplata', 'llave']

        google_id=session["user"].get('google_id')

        for cuenta in cuentas:
            numero= data.get(cuenta)
            if numero != 'null':
                acc= AccountRepository(name_account=cuenta, number_account=numero, google_id=google_id)
                account_exist=acc.is_exists()

                if account_exist:
                    account_exist.update(number_acc=numero)
                else:
                    acc.save()



        cellphone= data.get('cellphone')
        if data.get('cellphone'):
            if cellphone != 'null':
                user=UserModel.get_by_google_id(google_id=google_id);
                user.update(num_whatsapp=data.get('cellphone'));



        return jsonify({"status":'succes'}), 200
    except Exception as e:

        print(e)
        return jsonify({"status":'no succes'}), 501
  
    