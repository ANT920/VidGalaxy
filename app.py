import dropbox
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, Table, Column, BigInteger, Text, MetaData, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from datetime import datetime

# Загрузка переменных окружения из файла .env
load_dotenv()

app = Flask(__name__)

# Настройка клиента Dropbox
dropbox_access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
if not dropbox_access_token:
    raise ValueError("Нет токена доступа к Dropbox. Убедитесь, что переменная окружения DROPBOX_ACCESS_TOKEN установлена.")

dbx = dropbox.Dropbox(dropbox_access_token)

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
    Column('upload_date', TIMESTAMP(timezone=True))
)

# Создание таблицы в базе данных, если её нет
metadata.create_all(engine)

@app.route('/')
def home():
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
            filepath = f"/{filename}"
            dbx.files_upload(file.read(), filepath)

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
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(f"/{video.filename}")
        video_url = shared_link_metadata.url.replace("?dl=0", "?raw=1")
        return render_template('watch.html', video=video, video_url=video_url)
    return "Видео не найдено", 404

@app.route('/telegram')
def telegram():
    return render_template('telegram.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
