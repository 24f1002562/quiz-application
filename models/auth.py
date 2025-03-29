from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db
from datetime import datetime

auth = Blueprint('auth', __name__)

# Home page
@auth.route('/')
def home():
    return render_template('home.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                flash("Welcome back!", category='success')
                if user.is_admin:
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('views.dashboard'))
            else:
                flash('Wrong password!', category='error')
        else:
            flash('Email not found!', category='error')
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Goodbye!', category='success')
    return redirect(url_for('auth.home'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        dob = request.form.get('dob')
        qualification = request.form.get('qualification')
        password = request.form.get('password')
        confirm_password = request.form.get('cp')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already taken', category='error')
        elif password != confirm_password:
            flash('Passwords do not match', category='error')
        else:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                email=email,
                name=name,
                dob=dob_date,
                qualification=qualification,
                password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!', category='success')
            return redirect(url_for('auth.login'))
    return render_template("register.html", user=current_user)
