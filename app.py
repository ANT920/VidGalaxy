from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine, Table, Column, BigInteger, Text, MetaData, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from datetime import datetime
import requests
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
VIMEO_ACCESS_TOKEN = os.environ.get('VIMEO_ACCESS_TOKEN')
VIMEO_USER_ID = os.environ.get('VIMEO_USER_ID')

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
    Column('embed_link', Text),
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
        file = request.files['file']
        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Проверка существования файла и вывода сообщений
            if os.path.exists(filepath):
                print(f"File successfully saved at: {filepath}")
            else:
                print(f"Failed to save file at: {filepath}")

            # Загрузка файла на Vimeo и получение ссылки для встраивания
            try:
                print("Attempting to upload file to Vimeo...")
                headers = {
                    'Authorization': f'Bearer {VIMEO_ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                }
                upload_link_response = requests.post(
                    f'https://api.vimeo.com/users/{VIMEO_USER_ID}/videos',
                    headers=headers,
                    json={'upload': {'approach': 'tus', 'size': os.path.getsize(filepath)}}
                )
                upload_link_response.raise_for_status()
                upload_link = upload_link_response.json()['upload']['upload_link']
                
                with open(filepath, 'rb') as f:
                    tus_headers = headers.copy()
                    tus_headers.update({
                        'Upload-Offset': '0',
                        'Tus-Resumable': '1.0.0',
                        'Content-Length': str(os.path.getsize(filepath))
                    })
                    response = requests.patch(upload_link, headers=tus_headers, data=f)
                    response.raise_for_status()

                video_id = upload_link_response.json()['uri'].split('/')[-1]
                embed_link = f"https://player.vimeo.com/video/{video_id}"
                print(f"File successfully uploaded to Vimeo at: {embed_link}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to upload file to Vimeo: {e.response.text}")
                return f"Ошибка при загрузке файла в Vimeo: {e.response.text}", 500

            # Сохранение информации о видео в базу данных
            upload_date = datetime.now()
            new_video = videos.insert().values(title=title, embed_link=embed_link, upload_date=upload_date)
            try:
                with engine.connect() as connection:
                    print("Trying to save video information to database...")
                    transaction = connection.begin()
                    connection.execute(new_video)
                    transaction.commit()
                    print(f"Video information saved to database: {title}, {embed_link}, {upload_date}")
            except Exception as e:
                print(f"Error saving video information to database: {e}")
                return "Ошибка при сохранении информации о видео в базе данных", 500
            
            return redirect(url_for('upload'))
    return render_template('upload.html')

@app.route('/watch_video/<int:video_id>')
def watch_video(video_id):
    with engine.connect() as connection:
        video = connection.execute(videos.select().where(videos.c.id == video_id)).fetchone()
    if video:
        print(f"Video title: {video.title}")
        print(f"Vimeo embed link: {video.embed_link}")
        return render_template('watch.html', video=video)
    return "Видео не найдено", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
