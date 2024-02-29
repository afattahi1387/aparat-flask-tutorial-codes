import os
from flask import Flask, flash, request, Response, render_template, redirect, url_for, abort, session
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

# pip install Flask-Session
# from flask_session import Session

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = './uploaded_files/'
app.config.update(SECRET_KEY = 'xxx-yyy')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.username = str(self.id) + '_username'
        self.password = str(self.id) + '_password'
    
    def __repr__(self, id):
        return f"{str(self.id)}, {self.username}, {self.password}"

users = [User(id) for id in range(1, 6)]

def allow_to_files(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] == 'txt'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload-files', methods = ['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'uploaded_file' not in request.files:
            abort(404)
        uploaded_file = request.files['uploaded_file']
        if not uploaded_file or not uploaded_file.filename or not allow_to_files(uploaded_file.filename):
            abort(404)
        myfile = secure_filename(uploaded_file.filename)
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], myfile))
        flash("Your file uploaded successfully!")
        return redirect('/')
    else:
        return render_template('upload.html')

@app.route('/redirect-to-home')
def redirect_to_home():
    return redirect(url_for('hello'))

@app.route('/s/<int:id>')
def ss(id):
    return str(id)

@app.route('/hello')
def hello():
    flash('You are on hello page.')
    return 'flash message created.'

@app.route('/methods')
def methods():
    if request.args.get('param'):
        return request.args.get('param')
    else:
        return 'get method not found.'

@app.route('/post-methods', methods = ['GET', 'POST'])
def post_methods():
    if request.method == 'POST':
        return request.form['inp']
    else:
        return Response("""
            <form method='POST'><input type='text' name='inp'><input type='submit'></form>
        """)

@app.route('/dashboard')
@login_required
def dashboard():
    return 'dashboard'

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if '_username' in username and '_password' in password:
            id = int(username.split('_username')[0])
            user = User(id)
            login_user(user)
            flash('You are logged in.')
            return redirect(url_for('dashboard'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return 'You are logged out.'

@app.route('/set-session')
def set_session():
    session['city'] = 'Tehran'
    return Response("Your session set.")

@app.route('/get-session')
def get_session():
    return session['city']

@login_manager.user_loader
def user_load(id):
    return User(id)

@app.route('/create-an-error')
def create_an_error():
    abort(404)

@app.errorhandler(404)
def page_not_found(e):
    return Response("Page not found!")

if __name__ == '__main__':
    app.run(debug=True)
