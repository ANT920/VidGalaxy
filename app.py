import os
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import sqlite3
import hashlib

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['AVATAR_FOLDER'] = os.getenv('AVATAR_FOLDER', 'avatars')
app.secret_key = 'your_secret_key'

DATABASE_URL = 'vidgalaxy.db'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['AVATAR_FOLDER']):
    os.makedirs(app.config['AVATAR_FOLDER'])

def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY,
        url TEXT,
        username TEXT,
        title TEXT,
        avatarUrl TEXT,
        timestamp REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        username TEXT
    )
    ''')

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
    try:
        conn = sqlite3.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT url, username, title, avatarUrl FROM videos ORDER BY timestamp DESC")
        videos = [{'url': row[0], 'username': row[1], 'title': row[2], 'avatarUrl': row[3]} for row in c.fetchall()]
        conn.close()
        print("Fetched videos:", videos)  # Отладочная информация
        return jsonify({'videos': videos})
    except Exception as e:
        print("Error:", str(e))  # Отладочная информация
        return jsonify({'message': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'video' not in request.files:
            return jsonify({'message': 'Нет файла видео'}), 400
        file = request.files['video']
        if file.filename == '':
            return jsonify({'message': 'Пожалуйста, выберите файл'}), 400

        username = request.form['username']
        title = request.form['title']
        avatar = request.files.get('avatar')

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        avatar_url = None
        if avatar:
            avatar_path = os.path.join(app.config['AVATAR_FOLDER'], avatar.filename)
            avatar.save(avatar_path)
            avatar_url = f'/avatars/{avatar.filename}'

        video_data = {
            'url': f'/uploads/{file.filename}',
            'username': username,
            'title': title,
            'avatarUrl': avatar_url,
            'timestamp': os.path.getmtime(file_path)
        }
        conn = sqlite3.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("INSERT INTO videos (url, username, title, avatarUrl, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (video_data['url'], video_data['username'], video_data['title'], video_data['avatarUrl'], video_data['timestamp']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Видео успешно загружено'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/avatars/<filename>')
def uploaded_avatar(filename):
    return send_from_directory(app.config['AVATAR_FOLDER'], filename)

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        try:
            data = request.form
            email = data['email']
            password = data['password']
            username = data['username']

            print("Received registration data:", data)

            # Хешируем пароль
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            print("Registering user:", email, hashed_password)

            conn = sqlite3.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password, username) VALUES (?, ?, ?)",
                      (email, hashed_password, username))
            conn.commit()
            conn.close()

            return redirect(url_for('login_user'))
        except sqlite3.IntegrityError:
            print("IntegrityError: Этот email уже зарегистрирован.")
            return render_template('register.html', message='Этот email уже зарегистрирован.')
        except Exception as e:
            print("Error during registration:", str(e))
            return render_template('register.html', message=str(e))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        data = request.form
        print("Received login data:", data)
        email = data['email']
        password = data['password']
        
        # Хешируем пароль для проверки
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        print("Login attempt:", email, hashed_password)
        
        conn = sqlite3.connect('vidgalaxy.db')
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE email = ? AND password = ?", (email, hashed_password))
        user = c.fetchone()
        conn.close()
        
        if user:
            print("Login successful:", user)
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('profile'))
        else:
            print("Login failed: Неверный email или пароль.")
            return render_template('login.html', message='Неверный email или пароль.')
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'user_id' in session:
        user_id = session['user_id']
        username = session['username']
        return render_template('profile.html', user_id=user_id, username=username)
    else:
        return redirect(url_for('login_user'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
