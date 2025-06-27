from flask import Flask, render_template, g, request, session, redirect, url_for
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY']=os.urandom(24)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "sqlite3_db"):
        g.sqlite_db.close()

def get_user():
    user_results= None
    if 'user' in session:
        user = session['user']
        db = get_db()
        user_cur=db.execute('select id, name, password, expert, admin from users where name = ?', [user])
        user_results = user_cur.fetchone()
    return user_results

@app.route("/")
def index():
    user = get_user()
    db = get_db()
    questions_cur = db.execute('''select questions.id as question_id, 
                               questions.question_text, 
                               askers.name as asker_name, 
                               expert.name as expert_name from questions 
                               join users as askers on askers.id = questions.asked_by_id 
                               join users as expert on expert.id = questions.expert_id 
                               where questions.answer_text is not null''')
    questions_result = questions_cur.fetchall()
    return render_template("home.html", user= user, questions= questions_result)

@app.route("/login", methods=["GET", "POST"])
def login():
    user = get_user()
    error = None
    if request.method == "POST":
        db=get_db()
        name = request.form['name']
        password = request.form['password']
        user_cur=db.execute('select id, name, password from users where name = ?', [name])
        user_results = user_cur.fetchone()

        if user_results:
            if check_password_hash(user_results['password'], password):
                session['user'] = user_results['name']
                return redirect(url_for('index'))
            else:
                error = 'The password is incorrect!'
        else:
            error = "The username is incorrect!"    
        

    return render_template("login.html", user= user, error = error)

@app.route("/register", methods = ["GET", "POST"])
def register():
    user = get_user()
    if request.method == "POST":
        db=get_db()
        user_exist_cur = db.execute('select id from users where name = ?', [request.form['name']])
        existing_user = user_exist_cur.fetchone()
        if existing_user:
            return render_template('register.html', user= user, error="User already exist!")
        password_hashed = generate_password_hash(request.form['password'])
        db.execute('insert into users(name, password, expert, admin) values(?,?,?,?)',
                   [request.form['name'], password_hashed, 0, 0])
        db.commit()
        return redirect(url_for('login'))

    return render_template("register.html", user=user)

@app.route("/answer/<question_id>", methods = ["GET", "POST"])
def answer(question_id):
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    
    if user['expert'] == 0:
        return '<h1>You are not authorised to this page.</h1>'
    
    db = get_db()
    if request.method == "POST":
        db.execute('update questions set answer_text =? where id = ?',
                    [request.form['answer'], question_id])
        db.commit()
        return redirect(url_for('unanswered'))
    question_cur= db.execute('select id, question_text from questions where id = ?', [question_id])
    question= question_cur.fetchone()

    return render_template("answer.html", user= user, question = question)

@app.route("/ask", methods = ["POST","GET"])
def ask():
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == "POST":
        db.execute('insert into questions (question_text, asked_by_id, expert_id) values (?, ?, ?) ',
                    [request.form['question'], user['id'], request.form['expert']])
        db.commit()
        return redirect(url_for('ask'))
        
    expert_cur = db.execute('select id, name from users where expert = 1')
    expert_results = expert_cur.fetchall()
    return render_template("ask.html", user= user, experts= expert_results)

@app.route("/question/<question_id>")
def question(question_id):
    user = get_user()
    db = get_db()
    question_cur = db.execute('''select questions.question_text, 
                              questions.answer_text, 
                              askers.name as asker_name, 
                              expert.name as expert_name from questions 
                              join users as askers on askers.id = questions.asked_by_id 
                              join users as expert on expert.id = questions.expert_id 
                              where questions.id =?''', [question_id])
    question= question_cur.fetchone()
    return render_template("question.html", user= user, question= question)

@app.route("/unanswered")
def unanswered(): 
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    
    if user['expert'] == 0:
        return '<h1>You are not authorised to this page.</h1>'
    
    db= get_db()
    question_cur=db.execute('''select questions.id, 
                            questions.question_text, 
                            users.name from questions 
                            join users on users.id = questions.asked_by_id 
                            where questions.answer_text is null and questions.expert_id = ? ''',
                              [user['id']] )
    question_results= question_cur.fetchall()
    return render_template("unanswered.html", user= user, questions=question_results)

@app.route("/users")
def users():
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    
    if user['admin'] == 0:
        return '<h1>You are not authorised to this page.</h1>'
    
    db = get_db()
    user_cur=db.execute('select id, name, expert, admin from users')
    user_results = user_cur.fetchall()
    return render_template("users.html", user= user, users= user_results)

@app.route('/promote/<user_id>')
def promote(user_id):
    user = get_user()
    if not user:
        return redirect(url_for('login'))

    if user['admin'] == 0:
        return '<h1>You are not authorised to this page.</h1>'
     
    db= get_db()
    db.execute('update users set expert = 1 where id = ?', [user_id])
    db.commit()
    return redirect(url_for('users'))



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))



if __name__ == '__main__ ':
    app.run(debug= True)

