from flask import *
from flask_login import *
from .models import *
from . import db
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash

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
        subject = None

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

@admin.route('/subjects', methods=['GET'])
@login_required
@admin_required
def view_all_subjects():
    subjects = Subject.query.all()
    return render_template('admin/view_all_subjects.html', user=current_user, subjects=subjects)

@admin.route('/chapters', methods=['GET'])
@login_required
@admin_required
def view_all_chapters():
    chapters = Chapter.query.all()
    return render_template('admin/view_all_chapters.html', user=current_user, chapters=chapters)

@admin.route('/quizzes', methods=['GET'])
@login_required
@admin_required
def view_all_quizzes():
    quizzes = (
    db.session.query(Quiz, Chapter, Subject)
    .join(Chapter, Quiz.Chapter_id == Chapter.id)
    .join(Subject, Chapter.subject_id == Subject.id)
    .all() )
    return render_template('admin/view_all_quizzes.html', user=current_user, quizzes=quizzes)

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
        
        # Ensure values are properly converted to integers
        try:
            time_duration = int(time_duration)
            chapter_id = int(chapter_id)
        except (ValueError, TypeError):
            flash('Invalid input values. Please check your form entries.', category='error')
            return render_template('admin/quiz_form.html', user=current_user, subject=subject, chapters=chapters)
        
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
            
            try:
                db.session.commit()
                flash(f'Quiz "{title}" added successfully!', category='success')
                return redirect(url_for('admin.view_quiz', quiz_id=new_quiz.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating quiz: {str(e)}', category='error')
                print(f"Database error: {str(e)}")
    
    return render_template('admin/quiz_form.html', user=current_user, subject=subject, chapters=chapters)

@admin.route('/quiz/<int:quiz_id>/add_questions', methods=['GET', 'POST'])
@login_required
@admin_required
def add_questions(quiz_id):
    from .models import Quiz, Question
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        question_text = request.form.get('question')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        answer = request.form.get('answer')
        
        if not question_text or not option1 or not option2 or not option3 or not option4 or not answer:
            flash('All fields are required', category='error')
        else:
            new_question = Question(
                quiz_id=quiz_id,
                quest=question_text,
                option1=option1,
                option2=option2,
                option3=option3,
                option4=option4,
                answer=answer
            )
            db.session.add(new_question)
            db.session.commit()
            flash('Question added successfully!', category='success')
            if 'save_and_add' in request.form:
                return redirect(url_for('admin.add_questions', quiz_id=quiz_id))
            else:
                return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))
    existing_questions = Question.query.filter_by(quiz_id=quiz_id).all()
    questions_count = len(existing_questions)
    
    return render_template('admin/add_questions.html', 
                          user=current_user, 
                          quiz=quiz, 
                          questions_count=questions_count,
                          existing_questions=existing_questions)

@admin.route('/quiz/<int:quiz_id>/delete', methods=['GET'])
@login_required
@admin_required
def delete_quiz(quiz_id):
    from .models import Quiz, Question
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    for question in questions:
        db.session.delete(question)
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz and all its questions deleted successfully!', category='success')
    return redirect(url_for('admin.quizzes'))

@admin.route('/question/<int:question_id>/delete', methods=['GET'])
@login_required
@admin_required
def delete_question(question_id):
    from .models import Question
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', category='success')
    return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))

@admin.route('/delete/subject/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def delete_subject(subject_id):
    from .models import Subject
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully!', category='success')
    return redirect(url_for('admin.dashboard'))


@admin.route('/delete/chapter/<int:chapter_id>', methods=['POST'])
@login_required
@admin_required
def delete_chapter(chapter_id):
    from .models import Chapter
    chapter = Chapter.query.get_or_404(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully!', category='success')
    return redirect(url_for('admin.dashboard'))


@admin.route('/users')
@login_required
@admin_required
def users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', user=current_user, users=users)


@admin.route('/delete/user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    from .models import User
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', category='success')
    return redirect(url_for('admin.users'))

@admin.route('/edit/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    from .models import User
    edit_user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        edit_user.email = request.form.get('email')
        edit_user.name = request.form.get('name')
        edit_user.qualification = request.form.get('qualification')
        dob_str = request.form.get('dob')
        if dob_str:
            try:
                edit_user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format', 'error')
                return render_template('admin/edit_user.html', user=current_user, edit_user=edit_user)
        db.session.commit()
        flash('User updated successfully!', category='success')
        return redirect(url_for('admin.users'))
    return render_template('admin/edit_user.html', user=current_user, edit_user=edit_user)

@admin.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
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
            flash('Email already exists', category='error')
        elif password != cp:
            flash('Passwords don\'t match', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long', category='error')
        else:
            password1 = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(email=email, name=name, dob=dob_date, qualification=qualification, password=password1)
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', category='success')
            return redirect(url_for('admin.users'))
    return render_template('admin/add_user.html', user=current_user)

@admin.route('/view/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def view_quiz(quiz_id):
    from .models import Question, Quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template('admin/view_quiz.html', user=current_user, quiz=quiz, questions=questions)

@admin.route('/edit/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_quiz(quiz_id):
    from .models import Quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        quiz.title = request.form.get('title')
        quiz.description = request.form.get('description')
        quiz.time_duration = request.form.get('time_duration')
        db.session.commit()
        flash('Quiz updated successfully!', category='success')
        return redirect(url_for('admin.view_quiz', quiz_id=quiz_id))
    return render_template('admin/edit_quiz.html', user=current_user, quiz=quiz)

@admin.route('/edit/questions/<int:question_id>' , methods=['GET' , 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    from .models import Question
    question = Question.query.get_or_404(question_id)
    if request.method == 'POST':
        que = request.form.get('que')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        answer = request.form.get('answer')
        question.quest = que
        question.option1 = option1
        question.option2 = option2
        question.option3 = option3
        question.option4 = option4
        question.answer = answer
        db.session.commit()
        flash('Question updated successfully!', category='success')
        return redirect(url_for('admin.view_quiz', quiz_id=question.quiz_id))
    return render_template('admin/edit_question.html', user=current_user, question=question)

@admin.route('/edit/subject/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_subject(subject_id):
    from .models import Subject
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if not name:
            flash('Subject name is required!', category='error')
        else:
            subject.name = name
            subject.description = description
            db.session.commit()
            flash('Subject updated successfully!', category='success')
            return redirect(url_for('admin.view_all_subjects'))
    return render_template('admin/edit_subject.html', user=current_user, subject=subject)

@admin.route('/edit/chapter/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_chapter(chapter_id):
    from .models import Chapter
    chapter = Chapter.query.get_or_404(chapter_id)
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if not name:
            flash('Chapter name is required!', category='error')
        else:
            chapter.name = name
            chapter.description = description
            db.session.commit()
            flash('Chapter updated successfully!', category='success')
            return redirect(url_for('admin.view_all_chapters'))
    return render_template('admin/edit_chapter.html', user=current_user, chapter=chapter)
    

@admin.route('/add/chapter/subject', methods=['GET', 'POST'])
@login_required
@admin_required
def add_chapter_subject():
    from.models import Subject, Chapter
    subjects = Subject.query.all()
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        return redirect(url_for('admin.add_chapter', subject_id=subject_id))
    return render_template('admin/add_chapter_subject.html', user=current_user, subjects=subjects)

@admin.route('/search', methods=['GET'])
@login_required
@admin_required
def admin_search():
    query = request.args.get('query', '').strip()
    search_type = request.args.get('type', 'all')
    
    if not query:
        return render_template('admin/search.html', results=None)
    
    results = {
        'users': [],
        'subjects': [],
        'quizzes': [],
        'questions': []
    }
    
    if search_type in ['all', 'users']:
        results['users'] = User.query.filter(
            User.name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%')
        ).all()
    
    if search_type in ['all', 'subjects']:
        results['subjects'] = Subject.query.filter(
            Subject.name.ilike(f'%{query}%')
        ).all()
    
    if search_type in ['all', 'quizzes']:
        results['quizzes'] = db.session.query(Quiz, Chapter, Subject).join(
            Chapter, Quiz.Chapter_id == Chapter.id
        ).join(
            Subject, Chapter.subject_id == Subject.id
        ).filter(
            Quiz.title.ilike(f'%{query}%')
        ).all()
    
    if search_type in ['all', 'questions']:
        results['questions'] = Question.query.filter(
            Question.quest.ilike(f'%{query}%')
        ).all()
    
    return render_template(
        'admin/search.html',
        query=query,
        results=results,
        search_type=search_type
    )
        