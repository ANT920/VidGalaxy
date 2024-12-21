from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

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
    app.run(debug=True)

            file.save(filepath)
            
            # Сохранение информации о видео в Supabase через REST API
            data = {
                "title": video_title,
                "username": user_name,
                "filename": filename,
                "format": video_format
            }
            response = requests.post(f"{SUPABASE_URL}/rest/v1/videos", headers=SUPABASE_HEADERS, data=json.dumps(data))

            if response.status_code == 201:
                print("Video info saved successfully!")
            else:
                print(f"Failed to save video info: {response.text}")

            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/telegram')
def telegram():
    return render_template('telegram.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
