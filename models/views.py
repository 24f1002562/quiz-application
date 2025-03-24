from flask import *
from flask_login import *
from .models import *
from . import db
from datetime import datetime

views = Blueprint('views',__name__)

@views.route('/')
@login_required
def home():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    subjects = Subject.query.all()
    return render_template("home.html", user=current_user, subjects=subjects)