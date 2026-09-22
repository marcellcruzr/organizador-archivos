from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import os
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

UPLOAD_FOLDER = 'archivos_organizados'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_category(filename):
    ext = os.path.splitext(filename)[1].lower()
    categories = {
        'Documentos': {'.txt', '.doc', '.docx', '.pdf', '.odt', '.rtf'},
        'Imagenes': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'},
        'Videos': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'},
        'Audio': {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'},
        'Comprimidos': {'.zip', '.rar', '.7z', '.tar', '.gz'}
    }
    for category, extensions in categories.items():
        if ext in extensions:
            return category
    return 'Otros'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'success': False, 'error': 'No se seleccionaron archivos'}), 400
        
        results = []
        for file in files:
            if file.filename == '':
                continue
            
            filename = secure_filename(file.filename)
            category = get_category(filename)
            
            folder_path = os.path.join(UPLOAD_FOLDER, category)
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
        
        return jsonify({'success': True, 'files': results, 'message': f'{len(results)} archivos organizados'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ver-carpetas')
def ver_carpetas():
    try:
        base_path = Path(UPLOAD_FOLDER)
        estructura = {}
        
        if base_path.exists():
            for carpeta in base_path.iterdir():
                if carpeta.is_dir():
                    archivos = [f.name for f in carpeta.iterdir() if f.is_file()]
                    estructura[carpeta.name] = archivos
        
        return jsonify(estructura)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/descargar-organizado')
def descargar_organizado():
    try:
        base_path = Path(UPLOAD_FOLDER)
        
        if not base_path.exists() or not any(base_path.iterdir()):
            return jsonify({'error': 'No hay archivos organizados aún'}), 404
        
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for carpeta in base_path.iterdir():
                if carpeta.is_dir():
                    for archivo in carpeta.iterdir():
                        if archivo.is_file():
                            arcname = f"{carpeta.name}/{archivo.name}"
                            zf.write(archivo, arcname)
        
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='archivos_organizados.zip'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
