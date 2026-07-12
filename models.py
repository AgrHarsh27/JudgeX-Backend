from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(100), nullable = False, unique = True)
    password_hash = db.Column(db.String(100), nullable = False)
    is_admin = db.Column(db.Boolean,default=False)
    


class Problem(db.Model):
    __tablename__ = 'problems'
    id = db.Column(db.Integer,primary_key=True)
    problem_title = db.Column(db.String(100),nullable=False,unique=True)
    problem_statement = db.Column(db.Text,nullable=False)
    difficulty = db.Column(db.String(20),nullable=False)
    input_format = db.Column(db.Text,nullable=False)
    output_format = db.Column(db.Text,nullable=False)
    test_cases = db.relationship('TestCase',backref='problem',lazy=True)
    submissions =db.relationship('Submission',backref='problem',lazy=True)

class TestCase(db.Model):
    __tablename__ = 'test_cases'
    id = db.Column(db.Integer,primary_key = True)
    problem_id = db.Column(db.Integer,db.ForeignKey('problems.id'),nullable = False)
    input_data = db.Column(db.Text,nullable = False)
    expected_output = db.Column(db.Text,nullable = False)

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer,primary_key = True)
    problem_id = db.Column(db.Integer,db.ForeignKey('problems.id'),nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    source_code = db.Column(db.Text,nullable=False)
    language = db.Column(db.String(20),nullable = False)
    verdict = db.Column(db.String(20),nullable = False)
    execution_time = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime,default = db.func.now())
