import os
import secrets
import threading
import subprocess
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from firebase_admin import credentials, firestore, auth, initialize_app
from werkzeug.utils import secure_filename
from flask_cors import CORS
import time
import atexit


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(16))

CORS(app, supports_credentials=True)

cred = credentials.Certificate("firebase_credentials_data.json")
initialize_app(cred)
db = firestore.client()

UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max upload size


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        session['uploaded_resume'] = filename
        return jsonify({"message": "File uploaded successfully"}), 200
    else:
        return jsonify({"message": "Invalid file type"}), 400


def run_streamlit():
    subprocess.run(["streamlit", "run", "streamlit_app.py"])


threading.Thread(target=run_streamlit, daemon=True).start()


@app.route('/index2')
def index2():
    cache_buster = int(time.time())
    candidate_name = session.get('full_name', 'Candidate')
    email = session.get('email', '')
    return render_template('index2.html', candidate_name=candidate_name, email=email, cache_buster=cache_buster)


@app.route('/set_session')
def set_session():
    session['full_name'] = 'John Doe'
    session['email'] = 'johndoe@example.com'
    return 'Session data set!'


@app.route('/feedback')
def feedback():
    return render_template('feedback.html')


@app.route('/online_class')
def online_class():
    return render_template('online_class.html')


@app.route('/webinar')
def webinar():
    return render_template('webinar.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = auth.get_user_by_email(email)
            user_doc = db.collection('users').document(user.uid).get()
            if user_doc.exists:
                full_name = user_doc.to_dict()['full_name']

                session['full_name'] = full_name
                session['email'] = email

                return render_template('index.html')
            else:
                return jsonify({"message": "User not found"}), 404

        except Exception as e:
            return jsonify({"message": str(e)}), 400

    return render_template('login.html')


@app.route('/forgotpw')
def forgotpw():
    return render_template('forgotpw.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            data = request.json
            full_name = data['full_name']
            username = data['username']
            email = data['email']
            gender = data['gender']
            password = data['password']

            if not email or not password or not full_name:
                return jsonify({"message": "Missing required fields"}), 400

            user = auth.create_user(
                email=email,
                password=password
            )

            db.collection('users').document(user.uid).set({
                'full_name': full_name,
                'username': username,
                'email': email,
                'gender': gender
            })

            session['full_name'] = full_name
            session['email'] = email

            return jsonify({"message": "User created successfully"}), 201

        except Exception as e:
            return jsonify({"message": str(e)}), 400

    return render_template('signup.html')


@app.route('/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify(success=True, message="Logged out successfully")
    except Exception as e:
        return jsonify(success=False, message="Logout failed")

streamlit_process = None

def run_streamlit():
    global streamlit_process
    streamlit_process = subprocess.Popen([
        "streamlit", "run", "streamlit_app.py",
        "--server.port=8501",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--server.headless=true"
    ])

def cleanup():
    global streamlit_process
    if streamlit_process is not None:
        try:
            streamlit_process.terminate()
        except Exception:
            pass

atexit.register(cleanup)
threading.Thread(target=run_streamlit, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True)
