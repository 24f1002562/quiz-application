from flask import flask
from flask_login import UserMixin,LoginManager
from sqlalchemy import *
from os import path
from werkzeug.security import generate_password_hash,check_password_hash

db = SQLAlchemy()
DB_NAME = "quiz-app.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '24f1005262'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{quiz-app.db}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    l_manager = LoginManager()
    l_manager.login_view = 'auth.login'
    l_manager.init_app(app)
    from .models import User

    @l_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    from .auth import auth
    from .views import views
    from .admin import admin

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')

    create_database(app)
    create_admin(app)

    return app

def create_database(app):
    if not path.exists('quiz-app.db'):
        with app.app_context():
            db.create_all()
            print("Created Data-Base")


def create_admin(app):
    from .models import User
    db app.app_context():
    db.create_all()
    if not User.query.filter_by(email = '24f1002562@ds.study.iitm.ac.in').first():
        admin = User(
            email = '24f1002562@ds.study.iitm.ac.in'
            name = "Teja"
            password = "Teja@4569"
            qualification = "B-TECH"
            DOB = "07-07-2006"
        )
        db.session.app(admin)
        db.session.commit()
