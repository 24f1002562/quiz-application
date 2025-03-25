from flask import *
from flask_login import *
from .models import *
from . import db
from datetime import *
from functools import wraps

admin = Blueprint('admin',__name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', category='error')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.filter_by(is_admin=False).all()
    subjects = Subject.query.all()
    return render_template('admin/dashboard.html' , user=current_user, subjects=subjects, users=users)

@admin.route('/subject/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_subject():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        created_at = datetime.utcnow()
        if not name:
            flash('Subject name is required!', category='error')
        else:
            new_subject = Subject(name=name, description=description , created_at=created_at)
            db.session.add(new_subject)
            db.session.commit()
            flash(f'Subject "{name}" added successfully at {created_at}!', category='success')
            return redirect(url_for('admin.dashboard'))
    return render_template('admin/add_subject.html', user=current_user)

@admin.route('/chapter/add/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if not name:
            flash('Chapter name is required!', category='error')
        else:
            new_chapter = Chapter(name=name, description=description, subject_id=subject_id)
            db.session.add(new_chapter)
            db.session.commit()
            flash('Chapter added successfully!', category='success')
            return redirect(url_for('admin.dashboard'))
    return render_template('admin/add_chapter.html', user=current_user, subject=subject)