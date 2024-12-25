from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from sqlalchemy import create_engine, Table, Column, BigInteger, Text, MetaData, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from datetime import datetime
from sqlalchemy.sql import text
from flask_cors import CORS

# Загрузка переменных окружения из файла .env
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'server_uploads'

# Убедимся, что директория существует при каждом запуске
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    print(f"Created directory: {app.config['UPLOAD_FOLDER']}")

# Получение переменных окружения
DATABASE_URL = os.environ.get('DATABASE_URL')

# Создание подключения к базе данных
engine = create_engine(DATABASE_URL)

# Проверка подключения к базе данных
def check_database_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).fetchone()
            if result:
                print("Подключение к базе данных успешно!")
            else:
                print("Не удалось выполнить запрос к базе данных.")
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")

check_database_connection()

Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

# Определение таблицы videos
videos = Table(
    'videos', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('title', Text),
    Column('filename', Text),
    Column('upload_date', TIMESTAMP(timezone=True))
)

# Создание таблицы в базе данных, если её нет
metadata.create_all(engine)

@app.route('/')
def home():
    # Получение всех видео из базы данных
    with engine.connect() as connection:
        videos_data = connection.execute(videos.select()).fetchall()
    return render_template('index.html', videos=videos_data)

@app.route('/short')
def short():
    return render_template('short.html')

@app.route('/trending')
def trending():
    return render_template('trending.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        google_drive_url = request.form['google_drive_url']
        
        # Проверка существования ссылки и вывода сообщений
        if google_drive_url:
            print(f"Google Drive URL successfully received: {google_drive_url}")
            
            # Сохранение информации о видео в базу данных
            upload_date = datetime.now()
            new_video = videos.insert().values(title=title, filename=google_drive_url, upload_date=upload_date)
            try:
                with engine.connect() as connection:
                    print("Trying to save video information to database...")
                    transaction = connection.begin()
                    connection.execute(new_video)
                    transaction.commit()
                    print(f"Video information saved to database: {title}, {google_drive_url}, {upload_date}")
            except Exception as e:
                print(f"Error saving video information to database: {e}")
                return "Ошибка при сохранении информации о видео в базе данных", 500
            
            return redirect(url_for('upload'))
        else:
            return "Ссылка на Google Drive отсутствует", 400
    return render_template('upload.html')

@app.route('/watch_video/<int:video_id>')
def watch_video(video_id):
    with engine.connect() as connection:
        video = connection.execute(videos.select().where(videos.c.id == video_id)).fetchone()
    if video:
        print(f"Video title: {video.title}")
        print(f"Video filename (Google Drive URL): {video.filename}")
        return render_template('watch.html', video=video)
    return "Видео не найдено", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
