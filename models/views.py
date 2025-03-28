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
        
    quizzes = db.session.query(Quiz, Chapter, Subject)\
        .join(Chapter, Quiz.Chapter_id == Chapter.id)\
        .join(Subject, Chapter.subject_id == Subject.id)\
        .all()
    user_scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.timestamp_of_attempt).all()
    quizzes_taken = len(user_scores)
    if quizzes_taken > 0:
        total_score = sum(score.total_scored for score in user_scores)
        average_score = f"{(total_score / quizzes_taken):.1f}%"
    else:
        average_score = "0%"
    quiz_data = [{
        'id': quiz.id,
        'title': quiz.title,
        'subject': subject.name,
        'chapter': chapter.name,
        'duration': quiz.time_duration
    } for quiz, chapter, subject in quizzes]
    quiz_dates = [score.timestamp_of_attempt.strftime('%Y-%m-%d') for score in user_scores]
    quiz_scores = [score.total_scored for score in user_scores]
    subject_performance = {}
    for score in user_scores:
        quiz = Quiz.query.get(score.quiz_id)
        chapter = Chapter.query.get(quiz.Chapter_id)
        subject = Subject.query.get(chapter.subject_id)
        
        if subject.name not in subject_performance:
            subject_performance[subject.name] = {'total': 0, 'count': 0}
        
        subject_performance[subject.name]['total'] += score.total_scored
        subject_performance[subject.name]['count'] += 1
    
    subject_names = list(subject_performance.keys())
    subject_scores = [subject_performance[name]['total'] / subject_performance[name]['count']
                     for name in subject_names] if subject_names else []
    
    completed_quiz_ids = [score.quiz_id for score in user_scores]
    return render_template("user/user_dashboard.html",user=current_user,quizzes=quiz_data,quizzes_taken=quizzes_taken,average_score=average_score,available_quizzes=len(quizzes),quiz_dates=quiz_dates,quiz_scores=quiz_scores,subject_names=subject_names,subject_scores=subject_scores,completed_quiz_ids=completed_quiz_ids)

@views.route('/start_quiz/<int:quiz_id>')
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    session['quiz_start_time'] = datetime.utcnow().timestamp()
    session['quiz_duration'] = int(quiz.time_duration)
    current_time = datetime.utcnow().timestamp()
    return render_template('user/take_quiz.html',quiz=quiz,questions=questions,current_time=current_time)

@views.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    from .quiz_attempt import QuizAttempt
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    current_time = datetime.utcnow().timestamp()
    start_time = session.get('quiz_start_time')
    duration = session.get('quiz_duration')
    
    if not start_time or not duration:
        flash('Quiz session expired', 'error')
        return redirect(url_for('views.home'))
    
    time_taken = int(current_time - start_time)
    if time_taken > duration * 60:
        flash('Time is up! Quiz auto-submitted', 'warning')
        session.pop('quiz_start_time', None)
        session.pop('quiz_duration', None)
    
    score = 0
    new_score = Score(quiz_id=quiz_id, user_id=current_user.id, total_scored=0)
    db.session.add(new_score)
    db.session.flush()
    
    for question in questions:
        user_answer = request.form.get(f'question_{question.id}')
        if user_answer:
            user_answer = int(user_answer)
            attempt = QuizAttempt(score_id=new_score.id, question_id=question.id, user_answer=user_answer)
            db.session.add(attempt)
            if user_answer == question.answer:
                score += 1
    
    total_questions = len(questions)
    percentage_score = (score / total_questions) * 100 if total_questions > 0 else 0
    new_score.total_scored = percentage_score
    db.session.add(new_score)
    db.session.commit()
    flash(f'Quiz submitted! Your score: {percentage_score:.1f}%', 'success')
    return redirect(url_for('views.home'))

@views.route('/quiz_history')
@login_required
def quiz_history():
    # Get user's quiz attempts with detailed information
    quiz_history = db.session.query(
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

    # Get detailed answers for each quiz
    detailed_history = []
    for score, quiz, chapter, subject in quiz_history:
        # Get all questions and user answers for this attempt
        attempt_details = db.session.query(
            QuizAttempt, Question
        ).join(
            Question, QuizAttempt.question_id == Question.id
        ).filter(
            QuizAttempt.score_id == score.id
        ).all()

        quiz_data = {
            'score': score,
            'quiz': quiz,
            'chapter': chapter,
            'subject': subject,
            'questions': [
                {
                    'question': question,
                    'user_answer': attempt.user_answer,
                    'is_correct': attempt.user_answer == question.answer,
                    'correct_answer': question.answer
                }
                for attempt, question in attempt_details
            ]
        }
        detailed_history.append(quiz_data)

    # Calculate statistics
    total_quizzes = len(detailed_history)
    if total_quizzes > 0:
        average_score = sum(data['score'].total_scored for data in detailed_history) / total_quizzes
        best_score = max(data['score'].total_scored for data in detailed_history)
        worst_score = min(data['score'].total_scored for data in detailed_history)
    else:
        average_score = best_score = worst_score = 0

    stats = {
        'total_quizzes': total_quizzes,
        'average_score': round(average_score, 2),
        'best_score': best_score,
        'worst_score': worst_score
    }

    return render_template(
        'user/quiz_history.html',
        history=detailed_history,
        stats=stats
    )