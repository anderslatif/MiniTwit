from database.db_orm import Database
from repos.interfaces.auth_repo_interface import Auth_Repo_Interface
from repos.orm.implementations.models import User
database = Database()


class Auth_Repo(Auth_Repo_Interface):
    def check_if_user_exists(self, username):
        with database.connect_db() as db:
            user = db.query(User).filter_by(username=username).one_or_none()
            if user is not None:
                return True
            else:
                return False

    def validate_user(self, username):
        with database.connect_db() as db:
            user = db.query(User).filter_by(username=username).one_or_none()
            return user

    def register_user(self, username, email, password):
        with database.connect_db() as db:
            db_user = User(username=username, email=email, pw_hash=password)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user

    def change_user_password(self, password, user_id):
        # To implement
        pass


