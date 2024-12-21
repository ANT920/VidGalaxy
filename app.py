from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
import psycopg2
import requests
import json

# Загрузка переменных окружения из .env файла
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Инициализация переменных окружения для Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_HEADERS = {
    "Content-Type": "application/json",
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# Инициализация Postgres
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
DBNAME = os.getenv('DBNAME')

try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    print("Connection successful!")
    connection.close()
except Exception as e:
    print(f"Failed to connect: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/short')
def short():
    return render_template('short.html')

@app.route('/trending')
def trending():
    return render_template('trending.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        video_title = request.form['videoTitle']
        user_name = request.form['userName']
        video_format = request.form['videoFormat']
        file = request.files['videoUpload']
        
        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Сохранение информации о видео в Supabase через REST API
            data = {
                "title": video_title,
                "username": user_name,
                "filename": filename,
                "format": video_format
            }
            response = requests.post(f"{SUPABASE_URL}/rest/v1/videos", headers=SUPABASE_HEADERS, data=json.dumps(data))

            if response.status_code == 201:
                print("Video info saved successfully!")
            else:
                print(f"Failed to save video info: {response.text}")

            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/telegram')
def telegram():
    return render_template('telegram.html')

if __name__ == '__main__':
    app.run(debug=True)
