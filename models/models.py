from . import db
from flask_login import *
from datetime import datetime

class User(db.Model , UserMixin):
    id = db.Column(db.Integer , primary_key = True,autoincrement=True)
    email = db.Column(db.String(150) , unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    qualification = db.Column(db.String(150))
    dob = db.Column(db.String(10))
    is_admin = db.Column(db.Boolean, default=False)
    scores = db.relationship('Score', backref='user', lazy=True)
    is_admin = db.Column(db.Boolean, default=False)
    scores = db.relationship('Score', backref='user', lazy=True)

class Subject(db.Model , UserMixin):
    id = db.Column(db.Integer,primary_key = True , autoincrement=True)
    name = db.Column(db.String(150))
    description = db.Column(db.text)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    chapters = db.relationship('Chapter', backref='subject', lazy=True)

class Chapter(db.Model , UserMixin):
    id = db.Column(db.Integer,primary_key = True , autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)  # Foreign key to Subject
    quizzes = db.relationship('Quiz', backref='chapter', lazy=True)

class Quiz(db.Model , UserMixin):
    id = db.Column(db.Integer , primary_key = True,autoincrement=True)
    Chapter_id = db.Column(1db.Integer , db.ForeignKey('chapter.id'),nullable=False)
    date_of_quiz = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_duration = db.Column(db.String(5), nullable=False)
    remarks = db.Column(db.Text)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    scores = db.relationship('Score', backref='quiz', lazy=True)

class Question(db.Model,UserMixin):
    id = db.Column(db.Integer , primary_key = True,autoincrement=True)
    quiz_id = db.Column(db.Integer,db.ForeignKey('quiz.id'),nullable=False)
    quest = db.Column(db.Text,nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)  
    option4 = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Integer,nullable=Flase)

class Score(db.Model,UserMixin):
    id = db.Column(db.Integer , primary_key = True,autoincrement=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp_of_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    total_scored = db.Column(db.Integer, nullable=False)