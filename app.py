from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from sqlalchemy import create_engine, Table, Column, BigInteger, Text, MetaData, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from datetime import datetime
import dropbox
from sqlalchemy.sql import text

# Загрузка переменных окружения из файла .env
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'server_uploads'

# Убедимся, что директория существует при каждом запуске
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    print(f"Created directory: {app.config['UPLOAD_FOLDER']}")

# Получение переменных окружения
DATABASE_URL = os.environ.get('DATABASE_URL')
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')

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

            # Сохранение файла в Dropbox
            if DROPBOX_ACCESS_TOKEN:
                try:
                    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
                    with open(filepath, 'rb') as f:
                        dbx.files_upload(f.read(), f"/{filename}")
                    print(f"File successfully uploaded to Dropbox: {filename}")
                except Exception as e:
                    print(f"Failed to upload file to Dropbox: {e}")

            # Сохранение информации о видео в базу данных
            upload_date = datetime.now()
            new_video = videos.insert().values(title=title, filename=filename, upload_date=upload_date)
            with engine.connect() as connection:
                connection.execute(new_video)
            
            return redirect(url_for('upload'))
    return render_template('upload.html')

@app.route('/watch/<int:video_id>')
def watch(video_id):
    with engine.connect() as connection:
        video = connection.execute(videos.select().where(videos.c.id == video_id)).fetchone()
    if video:
        video_url = url_for('uploaded_file', filename=video.filename)
        return render_template('watch.html', video=video, video_url=video_url)
    return "Видео не найдено", 404

@app.route('/server_uploads/<filename>')
def uploaded_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        print(f"Serving file from: {filepath}")
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    print(f"File not found: {filepath}")
    return "Файл не найден", 404

@app.route('/telegram')
def telegram():
    return render_template('telegram.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
