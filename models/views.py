from flask import *
from flask_login import *
from .models import *
from . import db
from datetime import datetime
from sqlalchemy import func
from .quiz_attempt import QuizAttempt

views = Blueprint('views',__name__)

@views.route('/dashboard')
@login_required
def home():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    subjects = Subject.query.all()
    attempted_quizzes = set(
        score.quiz_id for score in Score.query.filter_by(user_id=current_user.id).all()
    )
    recent_attempts = db.session.query(
        Score, Quiz, Chapter, Subject
    ).join(
        Quiz, Score.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.Chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).filter(
        Score.user_id == current_user.id
    ).order_by(
        Score.timestamp_of_attempt.desc()
    ).limit(5).all()
    total_attempts = Score.query.filter_by(user_id=current_user.id).count()
    if total_attempts > 0:
        avg_score = db.session.query(func.avg(Score.total_scored))\
            .filter_by(user_id=current_user.id).scalar() or 0
        best_score = db.session.query(func.max(Score.total_scored))\
            .filter_by(user_id=current_user.id).scalar() or 0
    else:
        avg_score = best_score = 0
    subject_performance = {}
    for subject in subjects:
        scores = db.session.query(Score)\
            .join(Quiz)\
            .join(Chapter)\
            .filter(
                Score.user_id == current_user.id,
                Chapter.subject_id == subject.id
            ).all()
        
        if scores:
            avg = sum(score.total_scored for score in scores) / len(scores)
            subject_performance[subject.name] = avg
        else:
            subject_performance[subject.name] = 0

    return render_template(
        "user/user_dashboard.html",
        user=current_user,
        subjects=subjects,
        recent_attempts=recent_attempts,
        attempted_quizzes=attempted_quizzes,
        stats={
            'total_attempts': total_attempts,
            'avg_score': round(avg_score, 2),
            'best_score': round(best_score, 2)
        },
        subject_performance=subject_performance
    )

@views.route('/user/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    # Get basic statistics
    total_attempts = Score.query.filter_by(user_id=current_user.id).count()
    if total_attempts > 0:
        avg_score = db.session.query(func.avg(Score.total_scored))\
            .filter_by(user_id=current_user.id).scalar() or 0
        best_score = db.session.query(func.max(Score.total_scored))\
            .filter_by(user_id=current_user.id).scalar() or 0
    else:
        avg_score = best_score = 0
    
    return render_template(
        "user/dashboard.html",
        user=current_user,
        stats={
            'total_attempts': total_attempts,
            'avg_score': round(avg_score, 2),
            'best_score': round(best_score, 2)
        }
    )

@views.route('/user/subjects')
@login_required
def available_subjects():
    subjects = Subject.query.all()
    return render_template('user/subjects.html', subjects=subjects)

@views.route('/user/subject/<int:subject_id>/chapters')
@login_required
def subject_chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('user/chapters.html', subject=subject, chapters=chapters)

@views.route('/user/chapter/<int:chapter_id>/quizzes')
@login_required
def chapter_quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(Chapter_id=chapter_id).all()
    
    # Get attempted quizzes for current user
    attempted_quizzes = {
        score.quiz_id: score 
        for score in Score.query.filter_by(user_id=current_user.id).all()
    }
    
    return render_template(
        'user/quizzes.html',
        chapter=chapter,
        quizzes=quizzes,
        attempted_quizzes=attempted_quizzes
    )

@views.route('/user/recent-attempts')
@login_required
def recent_attempts():
    attempts = db.session.query(
        Score, Quiz, Chapter, Subject
    ).join(
        Quiz, Score.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.Chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).filter(
        Score.user_id == current_user.id
    ).order_by(
        Score.timestamp_of_attempt.desc()
    ).all()
    
    return render_template('user/recent_attempts.html', attempts=attempts)

@views.route('/quiz/<int:quiz_id>')
@login_required
def start_quiz(quiz_id):
    # Check if user has already attempted this quiz
    previous_attempt = Score.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).first()
    
    if previous_attempt:
        flash('You have already attempted this quiz. View your results in quiz history.', 'warning')
        return redirect(url_for('views.quiz_result', score_id=previous_attempt.id))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    session['quiz_start_time'] = datetime.utcnow().timestamp()
    session['quiz_duration'] = int(quiz.time_duration)
    return render_template('user/take_quiz.html', quiz=quiz, questions=questions)

@views.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    # Create score entry at the beginning
    new_score = Score(
        quiz_id=quiz_id,
        user_id=current_user.id,
        total_scored=0,
        timestamp_of_attempt=datetime.utcnow()
    )
    db.session.add(new_score)
    db.session.flush()
    
    score = 0
    total_questions = len(questions)
    print("\n=== QUIZ SUBMISSION DEBUG ===")
    
    for question in questions:
        user_answer = request.form.get(f'question_{question.id}')
        
        print(f"\nQuestion ID: {question.id}")
        print(f"Question: {question.quest}")
        print(f"Options:")
        print(f"1: {question.option1}")
        print(f"2: {question.option2}")
        print(f"3: {question.option3}")
        print(f"4: {question.option4}")
        print(f"Stored correct answer in DB: {question.answer}")
        print(f"User submitted answer: {user_answer}")
        
        if user_answer:
            try:
                # Convert user's numeric answer to option format
                user_option = f"option{user_answer}"
                print(f"Converted user answer to: {user_option}")
                print(f"Comparing with stored answer: {question.answer}")
                
                # Compare the string versions
                if user_option == question.answer:
                    score += 1
                    print("✓ CORRECT - Point awarded!")
                else:
                    print("✗ INCORRECT")
                
                # Save attempt
                attempt = QuizAttempt(
                    score_id=new_score.id,
                    question_id=question.id,
                    user_answer=int(user_answer)
                )
                db.session.add(attempt)
                
            except ValueError as e:
                print(f"Error converting answers: {e}")
                attempt = QuizAttempt(
                    score_id=new_score.id,
                    question_id=question.id,
                    user_answer=0
                )
                db.session.add(attempt)
        else:
            print("No answer submitted")
            attempt = QuizAttempt(
                score_id=new_score.id,
                question_id=question.id,
                user_answer=0
            )
            db.session.add(attempt)
    
    # Calculate percentage score
    percentage_score = (score / total_questions * 100) if total_questions > 0 else 0
    new_score.total_scored = percentage_score
    
    print("\n=== FINAL RESULTS ===")
    print(f"Total Questions: {total_questions}")
    print(f"Correct Answers: {score}")
    print(f"Final Score: {percentage_score}%")
    
    db.session.commit()
    
    flash(f'Quiz submitted! Your score: {percentage_score:.1f}%', 'success')
    return redirect(url_for('views.quiz_result', score_id=new_score.id))

@views.route('/quiz/result/<int:score_id>')
@login_required
def quiz_result(score_id):
    score = Score.query.get_or_404(score_id)
    if score.user_id != current_user.id:
        abort(403)
    
    quiz = Quiz.query.get(score.quiz_id)
    attempts = QuizAttempt.query.filter_by(score_id=score_id).all()
    questions = {attempt.question_id: Question.query.get(attempt.question_id) for attempt in attempts}
    
    return render_template(
        'user/quiz_result.html',
        score=score,
        quiz=quiz,
        attempts=attempts,
        questions=questions
    )

@views.route('/quiz/history')
@login_required
def quiz_history():
    # Get all quiz attempts with related information
    quiz_attempts = db.session.query(
        Score, Quiz, Chapter, Subject
    ).join(
        Quiz, Score.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.Chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).filter(
        Score.user_id == current_user.id
    ).order_by(
        Score.timestamp_of_attempt.desc()
    ).all()
    
    return render_template(
        'user/quiz_history.html',
        attempts=quiz_attempts
    )

@views.route('/debug/question/<int:question_id>')
@login_required
def debug_question(question_id):
    question = Question.query.get_or_404(question_id)
    return {
        'id': question.id,
        'question': question.quest,
        'options': [
            question.option1,
            question.option2,
            question.option3,
            question.option4
        ],
        'correct_answer': question.answer,
        'answer_type': str(type(question.answer))
    }

@views.route('/debug/quiz/<int:quiz_id>')
@login_required
def debug_quiz(quiz_id):
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    quiz_data = []
    for q in questions:
        quiz_data.append({
            'id': q.id,
            'question': q.quest,
            'options': {
                '1': q.option1,
                '2': q.option2,
                '3': q.option3,
                '4': q.option4
            },
            'stored_answer': q.answer,
            'answer_type': str(type(q.answer))
        })
    return jsonify(quiz_data)