from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap5 import Bootstrap

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)
bootstrap = Bootstrap(app)

from app import models, routes, forms

# === СОЗДАЁМ БАЗУ + ПОЛЬЗОВАТЕЛЕЙ ===
with app.app_context():
    db.create_all()

    # Админ
    if not models.User.query.filter_by(username='admin').first():
        admin = models.User(username='admin', is_admin=True)
        admin.set_password('password')
        db.session.add(admin)

    # МОЛы
    mols = ['419', 'Иванов', 'Петров', 'Сидоров', 'Козлов', 'Смирнов']
    for mol_name in mols:
        if not models.User.query.filter_by(username=mol_name).first():
            user = models.User(username=mol_name, is_admin=False)
            user.set_password('123')
            db.session.add(user)

    db.session.commit()