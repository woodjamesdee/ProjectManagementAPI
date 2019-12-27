from app import db

class User:
    """
    Internal representation of a User for the purposes of authentication. 
    """

    def __init__(self, firebase_token, firebase_user_id):
        self.firebase_token = firebase_token
        self.firebase_user_id = firebase_user_id

    @property
    def is_authenticated(self):
        value = db.child("Users").child(self.firebase_user_id).child("Authenticated").get(token=self.firebase_token).val()
        if value == "True":
            return True
        return False

    @is_authenticated.setter
    def is_authenticated(self, value):
        if value is True:
            db.child("Users").child(self.firebase_user_id).child("Authenticated").set("True", token=self.firebase_token)
        else:
            db.child("Users").child(self.firebase_user_id).child("Authenticated").set("False", token=self.firebase_token)

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.firebase_user_id)

    def is_admin(self):
        value = db.child("Users").child(self.firebase_user_id).child("Type").get(token=self.firebase_token).val()
        if value == "admin":
            return True
        else:
            return False

    def is_developer(self):
        value = db.child("Users").child(self.firebase_user_id).child("Type").get(token=self.firebase_token).val()
        if value == "developer":
            return True
        else:
            return False

    def is_client(self):
        value = db.child("Users").child(self.firebase_user_id).child("Type").get(token=self.firebase_token).val()
        if value == "client":
            return True
        else:
            return False

    def get_type(self):
        return db.child("Users").child(self.firebase_user_id).child("Type").get(token=self.firebase_token).val()