from .account_model import AccountModel

class AccountRepository(AccountModel):

    def __init__(self, name_account, number_account, google_id):
        self.name_acc= name_account
        self.number_acc=number_account
        self.google_id = google_id
    
    def is_exists(self):
        """
        Verifica si ya existe una cuenta con el mismo número y google_id.
        Devuelve True si no existe (se puede crear), False si ya existe.
        """
        existing = AccountModel.query.filter_by(name_acc=self.name_acc, google_id=self.google_id).first()
        return existing
          
        