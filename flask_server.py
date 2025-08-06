from flask import Flask, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)  

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return {'error': 'No file part in the request'}, 400

    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)
    return {'message': 'Resume uploaded successfully', 'path': save_path}, 200

if __name__ == '__main__':
    app.run(port=5000)
