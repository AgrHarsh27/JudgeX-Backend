from flask import Flask , jsonify , request
from models import db,User,Problem,Submission, TestCase
from judge import judge
from werkzeug.security import generate_password_hash , check_password_hash
import jwt
from datetime import datetime , timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///online_judge.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Super Secret'
db.init_app(app)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin')
    if not username or not password:
        return jsonify({
            'error': 'Username and password are required'
        }),400
    existing_user = User.query.filter_by(username = username).first()
    if(existing_user):
        return jsonify({
            'error': 'Username already exists'
        }),409
    hashed_password = generate_password_hash(password)
    if(username == 'admin'): is_admin = True
    new_user = User(username = username , password_hash = hashed_password, is_admin=is_admin)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({
        'message' : 'User successfully added'
    }),201


@app.route('/login', methods = ['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({
            'error': 'Username and Password required'
        }),400
    user = User.query.filter_by(username = username).first()
    if not user or not check_password_hash(user.password_hash , password):
        return jsonify({
            'error' : 'Invalid Credentials'
        }),401
    payload= {
        'user_id' : user.id ,
        'exp' : datetime.utcnow()+timedelta(hours=1)
    }
    token = jwt.encode(payload , app.config['SECRET_KEY'] , algorithm="HS256")
    return jsonify({
        'uId' : user.id,
        'token' : token,
        'isAdmin' : user.is_admin
    }),200
    
@app.route('/users')
def users():
    users = User.query.all()
    user_list = [
        {
            'id' : user.id,
            'username': user.username,
            'is_admin' : user.is_admin
        } for user in users
    ]
    return jsonify({'users': user_list})



@app.route('/problems')
def problems():
   problems = Problem.query.all()
   problem_list = [
         {
              'id': problem.id,
              'problem_title': problem.problem_title,
              'problem_statement': problem.problem_statement,
              'difficulty': problem.difficulty,
              'input_format': problem.input_format,
              'output_format': problem.output_format,
              'test_case_ids': [tc.id for tc in problem.test_cases],
              'submission_ids': [sub.id for sub in problem.submissions],

         } for problem in problems
   ]
   return jsonify({'problems': problem_list})



@app.route('/submit', methods=['POST'])
def submit():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({
            'error': 'Unauthorized Access'
        }),401
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0]!= "Bearer":
        return jsonify({
            'error' : 'Unauthorized Access'
        }),401
    token = parts[1]
    try:
        decode = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
        user_id = decode["user_id"]
    except:
        return jsonify({
            'error' : 'Unauthorized Access'
        }),401
    data = request.get_json()
    problem_id = data.get('problem_id')
    source_code = data.get('source_code')
    language = data.get('language')
    return jsonify(handle_submission(problem_id,source_code,language, user_id))


@app.route('/problems',methods=['POST'])
def add_problems():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({
            'error': 'Unauthorized Access'
        }),401
    parts = auth_header.split(" ")
    if len(parts)!=2 or parts[0] != "Bearer":
        return jsonify({
            'error' : 'Unauthorized Access'
        }),401
    token = parts[1]
    try : 
        decoded = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
        user_id = decoded["user_id"]
    except:
        return jsonify({
            'error' : 'Unauthorized Access'
        }),401
    user = User.query.filter_by(id = user_id).first()
    if not user or user.is_admin==False:
        return jsonify({
            'error' : 'Unauthorized Access'
        }),401
    
    data = request.get_json()
    problem_title = data.get('problem_title')
    problem_statement=data.get('problem_statement')
    difficulty =data.get('difficulty')
    input_format=data.get('input_format')
    output_format=data.get('output_format')
    if not problem_title or not problem_statement or not difficulty or not input_format or not output_format:
        return jsonify({
            'error': 'Please Fill all the fields'
        }),400
    new_problem = Problem(problem_title = problem_title,problem_statement=problem_statement,difficulty=difficulty,input_format=input_format,output_format=output_format)
    db.session.add(new_problem)
    db.session.commit()
    return jsonify({
        'message':  'Problem Successfully added',
        'problem_id' : new_problem.id
    }),200

@app.route('/problems/<int:problem_id>/testcases',methods=['POST'])
def add_testcase(problem_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({
            'error' : 'Unauthorized Access'
        }),401
    parts = auth_header.split(" ")
    if len(parts)!=2 or parts[0]!= "Bearer":
        return jsonify({
            'error' : 'Unauthorized Access'
        }),401
    token = parts[1]
    try :
        decoded = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
        user_id = decoded["user_id"]
    except:
        return jsonify({
            'error' : 'Unauthorized Access'
        }),401
    user = User.query.filter_by(id = user_id).first()
    if not user or not user.is_admin:
        return jsonify({
            'error' : 'Unauthorized Access'
        }),401
    problem = Problem.query.filter_by(id = problem_id).first()
    if not problem:
        return jsonify({
            'error' : 'Problem Does Not Exist'
        }),404
    data = request.get_json()
    input_data = data.get('input_data')
    expected_output = data.get('expected_output')
    if not input_data  or not expected_output:
        return jsonify({
            'error': 'Please fill all the fields'
        }),400
    new_testCase = TestCase(problem_id = problem_id, input_data = input_data ,expected_output=expected_output)
    db.session.add(new_testCase)
    db.session.commit()
    return jsonify({
        'message': 'TestCase successfully added to the problem'
    }),200
    


def handle_submission(problem_id,source_code,language,user_id):
    problem = Problem.query.filter_by(id = problem_id).first()
    if not problem:
        return {"status":"error","message":"Problem not found"}
    user = User.query.filter_by(id = user_id).first()
    if not user:
        return {"status":"error",
                "message": "User not found"}
    verdict , execution_time = judge(problem,source_code, language)
    submission = Submission(
        problem_id = problem_id,
        user_id = user_id,
        source_code= source_code,
        language= language,
        execution_time = execution_time,
        verdict= verdict    
    )
    db.session.add(submission)
    db.session.commit()
    return {"status": "success", "verdict": verdict , "execution_time": execution_time}



    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0',port=6000,debug=True)