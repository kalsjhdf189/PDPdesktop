import bcrypt
from datebase import Employee, Connect
from sqlalchemy import update

def hash_password():
    db = Connect.create_connection()
    
    users = db.query(Employee).all()
    for user in users:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(user.Пароль.encode(), salt)
        user.Пароль = hashed_password.decode()
    db.commit()
    
hash_password()