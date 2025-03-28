from . import db
from flask_login import UserMixin

class QuizAttempt(db.Model, UserMixin):
    __tablename__ = 'quiz_attempt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    score_id = db.Column(db.Integer, db.ForeignKey('score.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(db.Integer, nullable=False)
    
    # Relationships
    score = db.relationship('Score', backref=db.backref('attempts', lazy=True))
    question = db.relationship('Question')