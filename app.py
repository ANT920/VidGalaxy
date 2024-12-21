from flask import Flask, render_template
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из файла .env
load_dotenv()

app = Flask(__name__)

# Получение переменных окружения
DATABASE_URL = os.environ.get('DATABASE_URL')

# Создание подключения к базе данных
engine = create_engine(DATABASE_URL)

@app.route('/')
def home():
    try:
        # Пример запроса к базе данных
        result = engine.execute("SELECT 1")
        data = result.fetchone()
        connection_status = "Connection successful!"
    except Exception as e:
        connection_status = f"Connection failed: {str(e)}"
    
    return render_template('index.html', connection_status=connection_status)

@app.route('/short')
def short():
    return render_template('short.html')

@app.route('/trending')
def trending():
    return render_template('trending.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/telegram')
def telegram():
    return render_template('telegram.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
