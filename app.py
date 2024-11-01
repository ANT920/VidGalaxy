import psycopg2
from flask import Flask, render_template, request, jsonify, send_from_directory
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
AVATAR_FOLDER = 'avatars'
DATABASE_URL = os.environ.get('DATABASE_URL')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(AVATAR_FOLDER):
    os.makedirs(AVATAR_FOLDER)

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS videos
                 (id SERIAL PRIMARY KEY,
                 url TEXT,
                 username TEXT,
                 title TEXT,
                 avatarUrl TEXT,
                 timestamp REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id SERIAL PRIMARY KEY,
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
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT url, username, title, avatarUrl FROM videos ORDER BY timestamp DESC")
    videos = [{'url': row[0], 'username': row[1], 'title': row[2], 'avatarUrl': row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify({'videos': videos})

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'message': 'Нет файла видео'}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({'message': 'Пожалуйста, выберите файл'}), 400
    
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
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("INSERT INTO videos (url, username, title, avatarUrl, timestamp) VALUES (%s, %s, %s, %s, %s)",
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

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        try:
            data = request.form
            email = data['email']
            password = data['password']
            username = data['username']
            
            print("Received registration data:", data)

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            print("Registering user:", email, hashed_password)
            
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password, username) VALUES (%s, %s, %s)",
                      (email, hashed_password, username))
            conn.commit()
            conn.close()
            
            return redirect(url_for('login_user'))
        except psycopg2.IntegrityError:
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
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        print("Login attempt:", email, hashed_password)
        
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE email = %s AND password = %s", (email, hashed_password))
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
