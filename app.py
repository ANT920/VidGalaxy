from flask import Flask, render_template, request, jsonify, send_from_directory
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

videos = []

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
    sorted_videos = sorted(videos, key=lambda k: k['timestamp'], reverse=True)
    return jsonify({'videos': sorted_videos})

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
    videos.append(video_data)
    return jsonify({'url': f'/uploads/{file.filename}'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
