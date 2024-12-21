from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from sqlalchemy import create_engine, Table, Column, BigInteger, Text, MetaData, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from datetime import datetime

# Загрузка переменных окружения из файла .env
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'server_uploads'

# Убедимся, что директория существует
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    # Получение всех видео из базы данных
    videos_data = engine.execute(videos.select()).fetchall()
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

            # Сохранение информации о видео в базу данных
            upload_date = datetime.now()
            new_video = videos.insert().values(title=title, filename=filename, upload_date=upload_date)
            engine.execute(new_video)
            
            return redirect(url_for('upload'))
    return render_template('upload.html')

@app.route('/watch/<int:video_id>')
def watch(video_id):
    video = engine.execute(videos.select().where(videos.c.id == video_id)).fetchone()
    if video:
        video_url = url_for('uploaded_file', filename=video.filename)
        return render_template('watch.html', video=video, video_url=video_url)
    return "Видео не найдено", 404

@app.route('/server_uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/telegram')
def telegram():
    return render_template('telegram.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
