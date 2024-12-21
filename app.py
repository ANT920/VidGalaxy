import base64
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, Table, Column, BigInteger, Text, MetaData, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from datetime import datetime

# Загрузка переменных окружения из файла .env
load_dotenv()

app = Flask(__name__)

# Получение переменных окружения
DATABASE_URL = os.environ.get('DATABASE_URL')

# Создание подключения к базе данных
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

# Определение таблицы videos
videos = Table(
    'videos', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('title', Text),
    Column('filename', Text),
    Column('video_data', Text),
    Column('upload_date', TIMESTAMP(timezone=True))
)

# Создание таблицы в базе данных, если её нет
metadata.create_all(engine)

@app.route('/')
def home():
    try:
        # Пример запроса к базе данных
        result = engine.execute("SELECT 1")
        data = result.fetchone()
        connection_status = "Connection successful!"
        print(f"Connection successful: {data}")

        # Получение всех видео из базы данных
        videos_data = engine.execute(videos.select()).fetchall()
        print(f"Fetched videos: {videos_data}")
    except Exception as e:
        connection_status = f"Connection failed: {str(e)}"
        print(f"Connection failed: {str(e)}")
        videos_data = []
    
    return render_template('index.html', connection_status=connection_status, videos=videos_data)

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
            video_data = base64.b64encode(file.read()).decode('utf-8')  # Кодируем содержимое файла в base64

            # Сохранение информации о видео в базу данных
            upload_date = datetime.now()
            new_video = videos.insert().values(title=title, filename=filename, video_data=video_data, upload_date=upload_date)
            engine.execute(new_video)
            
            print(f"File uploaded and data saved: {filename}")
            return redirect(url_for('upload'))
    return render_template('upload.html')

@app.route('/watch/<int:video_id>')
def watch(video_id):
    video = engine.execute(videos.select().where(videos.c.id == video_id)).fetchone()
    if video:
        video_data = base64.b64decode(video.video_data)  # Декодируем base64 строку в байты
        video_url = url_for('video_data', video_id=video_id)  # Генерируем URL для видео данных
        return render_template('watch.html', video=video, video_url=video_url)
    return "Видео не найдено", 404

@app.route('/video_data/<int:video_id>')
def video_data(video_id):
    video = engine.execute(videos.select().where(videos.c.id == video_id)).fetchone()
    if video:
        video_data = base64.b64decode(video.video_data)  # Декодируем base64 строку в байты
        return video_data, {
            'Content-Type': 'video/mp4',
            'Content-Disposition': f'inline; filename="{video.filename}"'
        }
    return "Видео не найдено", 404

@app.route('/telegram')
def telegram():
    return render_template('telegram.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
