from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, Table, Column, BigInteger, Text, MetaData, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from dotenv import load_dotenv
from flask_cors import CORS
from datetime import datetime
import os

# Загрузка .env переменных
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'server_uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    print(f"Created upload folder: {app.config['UPLOAD_FOLDER']}")

# Подключение к базе данных
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

# Проверка соединения
def check_database_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ Подключение к базе данных установлено")
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")

check_database_connection()

# Определение таблицы videos
videos = Table(
    'videos', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('title', Text),
    Column('embed_link', Text),  # Будет заменён на Telegram-ссылку
    Column('upload_date', TIMESTAMP(timezone=True))
)

metadata.create_all(engine)

@app.route('/')
def home():
    with engine.connect() as conn:
        videos_data = conn.execute(videos.select()).fetchall()
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
        file = request.files['file']
        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            print(f"📁 Файл сохранён: {filepath}")

            # Пока заглушка — здесь позже добавим загрузку в Telegram
            embed_link = "https://example.com/fake-link"  # Заменим на реальную ссылку из Telegram

            upload_date = datetime.now()
            new_video = videos.insert().values(title=title, embed_link=embed_link, upload_date=upload_date)

            try:
                with engine.connect() as conn:
                    conn.execute(new_video)
                    print(f"🎥 Видео '{title}' добавлено в базу")
            except Exception as e:
                print(f"❌ Ошибка записи в БД: {e}")
                return "Ошибка при сохранении информации о видео", 500

            return redirect(url_for('upload'))

    return render_template('upload.html')

@app.route('/watch_video/<int:video_id>')
def watch_video(video_id):
    with engine.connect() as conn:
        video = conn.execute(videos.select().where(videos.c.id == video_id)).fetchone()
    if video:
        return render_template('watch.html', video=video)
    return "Видео не найдено", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
