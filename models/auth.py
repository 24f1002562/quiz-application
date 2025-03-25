from flask import *
from flask_login import *
from werkzeug.security import *
from .models import User
from . import db
from .models import User 
from datetime import datetime

auth = Blueprint('auth', __name__)


@auth.route('/')
def home():
    return render_template('home.html')
@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email = email).first()
        if user:
            if check_password_hash(password,user.password):
                flash("Login Successful",category ='Success' )
                login_user(user,remember=True)
                if user.is_admin:
                    return redirect(url_for('admin-dashboard'))
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('User does not exist.', category='error')
    return render_template("login.html",user = current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('views.home')

@auth.route('/register',methods = ['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        dob = request.form.get('dob')
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        qualification = request.form.get('qualification')
        password = request.form.get('password')
        cp = request.form.get('cp')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exits',category='error')
        elif password != cp:
            flash('Password\'s don\'t match')
        else:
            password1 = generate_password_hash(password,method='pbkdf2:sha256')
            new_user = User(email = email , name = name , dob = dob_date , qualification = qualification , password = password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account Created Successfully' , category = 'success')
            return redirect(url_for('views.home'))
    return render_template("register.html", user=current_user)
