from flask import *
from flask_login import *
from .models import *
from . import db
from datetime import datetime
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
            new_subject = Subject(name=name, description=description , created_time=created_at)
            db.session.add(new_subject)
            db.session.commit()
            flash(f'Subject "{name}" added successfully at {created_at}!', category='success')
            return redirect(url_for('admin.dashboard'))
    return render_template('admin/add_subject.html', user=current_user)

@admin.route('/chapter/add', defaults={'subject_id': None}, methods=['GET', 'POST'])
@admin.route('/chapter/add/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_chapter(subject_id):
    if subject_id:
        subject = Subject.query.get_or_404(subject_id)
    else:
        subject = None  # No subject assigned

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

    return render_template('admin/add_chapter.html', user=current_user, subject=subject , subject_id=subject_id)

@admin.route('/quizzes', methods=['GET', 'POST'])
@login_required
@admin_required
def quizzes():
    quizzes = (
    db.session.query(Quiz, Chapter, Subject)
    .join(Chapter, Quiz.Chapter_id == Chapter.id)
    .join(Subject, Chapter.subject_id == Subject.id)
    .all() )
    return render_template('admin/quizzes.html', user=current_user, quizzes=quizzes)

@admin.route('/quiz/add/subject', methods=['GET', 'POST'])
@login_required
@admin_required
def select_subject():
    from .models import Subject, Chapter
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        return redirect(url_for('admin.quiz_form', subject_id=subject_id))
    return render_template('admin/select_subject.html', user=current_user, subjects=subjects, chapters=chapters)

@admin.route('/quiz/add/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def quiz_form(subject_id):
    from .models import Quiz, Chapter, Subject
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        chapter_id = request.form.get('chapter_id')
        time_duration = request.form.get('time_duration')
        
        if not title:
            flash('Quiz title is required!', category='error')
        else:
            new_quiz = Quiz(
                title=title, 
                description=description, 
                Chapter_id=chapter_id,
                time_duration=time_duration
            )
            db.session.add(new_quiz)
            db.session.commit()
            flash(f'Quiz "{title}" added successfully!', category='success')
            return redirect(url_for('admin.quizzes'))
    
    return render_template('admin/quiz_form.html', user=current_user, subject=subject, chapters=chapters)