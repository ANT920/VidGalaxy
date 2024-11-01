import sqlite3
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import hashlib

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
AVATAR_FOLDER = 'avatars'
DATABASE = 'database.db'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(AVATAR_FOLDER):
    os.makedirs(AVATAR_FOLDER)

# Функция инициализации базы данных
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS videos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 url TEXT,
                 username TEXT,
                 title TEXT,
                 avatarUrl TEXT,
                 timestamp REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 email TEXT UNIQUE,
                 password TEXT,
                 username TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/videos')
def videos_page():
    return render_template('videos.html')

@app.route('/videos_data', methods=['GET'])
def get_videos():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT url, username, title, avatarUrl FROM videos ORDER BY timestamp DESC")
    videos = [{'url': row[0], 'username': row[1], 'title': row[2], 'avatarUrl': row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify({'videos': videos})

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['video']
    username = request.form['username']
    title = request.form['title']
    avatar = request.files.get('avatar')

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    avatar_url = None
    if avatar:
        avatar_path = os.path.join(AVATAR_FOLDER, avatar.filename)
        avatar.save(avatar_path)
        avatar_url = f'/avatars/{avatar.filename}'

    video_data = {
        'url': f'/uploads/{file.filename}',
        'username': username,
        'title': title,
        'avatarUrl': avatar_url,
        'timestamp': os.path.getmtime(file_path)
    }
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO videos (url, username, title, avatarUrl, timestamp) VALUES (?, ?, ?, ?, ?)",
              (video_data['url'], video_data['username'], video_data['title'], video_data['avatarUrl'], video_data['timestamp']))
    conn.commit()
    conn.close()
    return jsonify({'url': f'/uploads/{file.filename}'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/avatars/<filename>')
def uploaded_avatar(filename):
    return send_from_directory(AVATAR_FOLDER, filename)

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    email = data['email']
    password = data['password']
    username = data['username']
    
    # Хешируем пароль
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password, username) VALUES (?, ?, ?)",
                  (email, hashed_password, username))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'status': 'fail', 'message': 'Этот email уже зарегистрирован.'}), 400
    finally:
        conn.close()
    
    return jsonify({'status': 'success', 'message': 'Регистрация успешна.'})

@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email = data['email']
    password = data['password']
    
    # Хешируем пароль для проверки
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE email = ? AND password = ?", (email, hashed_password))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({'status': 'success', 'message': 'Вход успешен.', 'user_id': user[0], 'username': user[1]})
    else:
        return jsonify({'status': 'fail', 'message': 'Неверный email или пароль.'}), 401

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
