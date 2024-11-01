import sqlite3
from flask import Flask, render_template, request, jsonify, send_from_directory
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
AVATAR_FOLDER = 'avatars'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(AVATAR_FOLDER):
    os.makedirs(AVATAR_FOLDER)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS videos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 url TEXT,
                 username TEXT,
                 title TEXT,
                 timestamp REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT,
                 avatar TEXT)''')
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
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT videos.url, videos.username, videos.title, users.avatar
                 FROM videos
                 JOIN users ON videos.username = users.username
                 ORDER BY videos.timestamp DESC''')
    videos = [{'url': row[0], 'username': row[1], 'title': row[2], 'avatar': row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify({'videos': videos})

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['video']
    username = request.form['username']
    title = request.form['title']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    video_data = {
        'url': f'/uploads/{file.filename}',
        'username': username,
        'title': title,
        'timestamp': os.path.getmtime(file_path)
    }
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO videos (url, username, title, timestamp) VALUES (?, ?, ?, ?)",
              (video_data['url'], video_data['username'], video_data['title'], video_data['timestamp']))
    conn.commit()
    conn.close()
    return jsonify({'url': f'/uploads/{file.filename}'})

@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    file = request.files['avatar']
    username = request.form['username']
    file_path = os.path.join(AVATAR_FOLDER, file.filename)
    file.save(file_path)
    avatar_url = f'/avatars/{file.filename}'
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (username, avatar) VALUES (?, ?)",
              (username, avatar_url))
    conn.commit()
    conn.close()
    return jsonify({'avatar': avatar_url})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/avatars/<filename>')
def uploaded_avatar(filename):
    return send_from_directory(AVATAR_FOLDER, filename)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)