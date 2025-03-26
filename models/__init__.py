from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
DB_NAME = "quiz-app.db"

def create_app():
    app = Flask(__name__, template_folder=r'C:\Users\DELL\OneDrive\Desktop\quiz-app(final)\quiz-application\templates')
    app.config['SECRET_KEY'] = '24f1005262'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from .models import User  # Ensure this is inside create_app

    l_manager = LoginManager()
    l_manager.login_view = 'auth.login'
    l_manager.init_app(app)

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
    create_admin(app)  # User must be available when this runs

    return app

def create_database(app):
    with app.app_context():
        db.create_all()
        print("Created Database")

def create_admin(app):
    from .models import User

    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="24f1002562@ds.study.iitm.ac.in").first():
            password1 = generate_password_hash("24f1002562", method='pbkdf2:sha256')
            admin = User(
                email="24f1002562@ds.study.iitm.ac.in",
                name="Teja",
                password = password1,
                qualification="B-TECH",
                dob=datetime.strptime("07-07-2006", "%d-%m-%Y").date(),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
