from . import db
from flask_login import UserMixin
from datetime import datetime

# User table - stores user information
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    qualification = db.Column(db.String(150))
    dob = db.Column(db.Date)
    is_admin = db.Column(db.Boolean, default=False)
    # Link to scores
    scores = db.relationship('Score', backref='user')

# Subject table - stores subjects
class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.Text)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    # Link to chapters
    chapters = db.relationship('Chapter', backref='subject', cascade='all, delete')

# Chapter table - stores chapters for each subject
class Chapter(db.Model):
    __tablename__ = 'chapter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    # Link to quizzes
    quizzes = db.relationship('Quiz', backref='chapter', cascade='all, delete')

# Quiz table - stores quizzes for each chapter
class Quiz(db.Model):
    __tablename__ = 'quiz'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    Chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'))
    time_duration = db.Column(db.Integer)  # in minutes
    date_of_quiz = db.Column(db.DateTime, default=datetime.utcnow)
    # Links to questions and scores
    questions = db.relationship('Question', backref='quiz', cascade='all, delete')
    scores = db.relationship('Score', backref='quiz', cascade='all, delete')

# Question table - stores questions for each quiz
class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    quest = db.Column(db.Text)
    option1 = db.Column(db.String(255))
    option2 = db.Column(db.String(255))
    option3 = db.Column(db.String(255))
    option4 = db.Column(db.String(255))
    answer = db.Column(db.Integer)  # 1, 2, 3, or 4

# Score table - stores quiz scores
class Score(db.Model):
    __tablename__ = 'score'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_scored = db.Column(db.Float)  # percentage score
    timestamp_of_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    # Link to quiz attempts
    quiz_attempts = db.relationship('QuizAttempt', backref='score', cascade='all, delete')

# QuizAttempt table - stores individual question attempts
class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempt'
    id = db.Column(db.Integer, primary_key=True)
    score_id = db.Column(db.Integer, db.ForeignKey('score.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    user_answer = db.Column(db.Integer)  # 1, 2, 3, or 4
    # Link to question
    question = db.relationship('Question')