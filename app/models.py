from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    barcode = db.Column(db.String(64), unique=True, nullable=False)
    location = db.Column(db.String(128))
    status = db.Column(db.String(64), default='на балансе')
    responsible_person = db.Column(db.String(128))
    acquisition_date = db.Column(db.DateTime, default=datetime.utcnow)
    writeoff_date = db.Column(db.DateTime)
    inventory_number = db.Column(db.String(64))
    cost = db.Column(db.Float)