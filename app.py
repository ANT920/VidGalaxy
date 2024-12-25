from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from sqlalchemy import create_engine, Table, Column, BigInteger, Text, MetaData, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from datetime import datetime
import dropbox
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
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')

if DROPBOX_ACCESS_TOKEN:
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        account_info = dbx.users_get_current_account()
        print(f"Successfully connected to Dropbox account: {account_info.name.display_name}")
    except Exception as e:
        print(f"Failed to connect to Dropbox: {e}")
else:
    print("Dropbox access token is missing.")

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

            # Сохранение файла в Dropbox в папке videos_server и получение URL
            if DROPBOX_ACCESS_TOKEN:
                try:
                    print("Attempting to upload file to Dropbox...")
                    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
                    dropbox_path = f"/videos_server/{filename}"
                    with open(filepath, 'rb') as f:
                        response = dbx.files_upload(f.read(), dropbox_path)
                    shared_link_metadata = dbx.sharing_create_shared_link_with_settings(dropbox_path)
                    dropbox_url = shared_link_metadata.url.replace("?dl=0", "?raw=1")
                    print(f"File successfully uploaded to Dropbox at: {dropbox_url}")
                except Exception as e:
                    print(f"Failed to upload file to Dropbox: {e}")
                    return "Ошибка при загрузке файла в Dropbox", 500
            else:
                print("Dropbox access token is missing.")
                return "Токен доступа Dropbox отсутствует", 500

            # Сохранение информации о видео в базу данных
            upload_date = datetime.now()
            new_video = videos.insert().values(title=title, filename=dropbox_url, upload_date=upload_date)
            try:
                with engine.connect() as connection:
                    print("Trying to save video information to database...")
                    transaction = connection.begin()
                    connection.execute(new_video)
                    transaction.commit()
                    print(f"Video information saved to database: {title}, {dropbox_url}, {upload_date}")
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
        print(f"Video filename (Dropbox URL): {video.filename}")
        return render_template('watch.html', video=video)
    return "Видео не найдено", 404

@app.route('/get_temporary_link/<int:video_id>')
def get_temporary_link(video_id):
    with engine.connect() as connection:
        video = connection.execute(videos.select().where(videos.c.id == video_id)).fetchone()
    if video:
        try:
            dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
            dropbox_path = video.filename.replace("https://www.dropbox.com", "").replace("?raw=1", "")
            print(f"Attempting to get temporary link for path: {dropbox_path}")
            temp_link_metadata = dbx.files_get_temporary_link(dropbox_path)
            temp_link = temp_link_metadata.link
            print(f"Temporary link obtained: {temp_link}")
            return jsonify({'temporary_link': temp_link})
        except Exception as e:
            print(f"Error getting temporary link: {e}")
            return f"Ошибка при получении временной ссылки: {e}", 500
    return "Видео не найдено", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
