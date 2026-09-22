import os
import uuid
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'archivos_organizados'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CATEGORIES = {
    'Imagenes': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'},
    'Documentos': {'.pdf', '.doc', '.docx', '.txt', '.xlsx', '.csv', '.pptx', '.md'},
    'Videos': {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv'},
    'Audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg'},
    'Archivos': {'.zip', '.rar', '.7z', '.tar', '.gz', '.iso'}
}

def get_category(filename):
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return 'Otros'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')
    results = []
    
    for file in files:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        category = get_category(filename)
        
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], category)
        os.makedirs(folder_path, exist_ok=True)
        
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:6]}{ext}"
        save_path = os.path.join(folder_path, unique_filename)
        
        file.save(save_path)
        results.append({
            'original': file.filename,
            'saved_as': unique_filename,
            'folder': category
        })

    return jsonify({'success': True, 'files': results})

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
