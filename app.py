import os
import uuid
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import zipfile
from io import BytesIO
from pathlib import Path

app = Flask(__name__)

# Configuración de subida de archivos
UPLOAD_FOLDER = 'archivos_organizados'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Crear carpeta de subida si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/organizar', methods=['POST'])
def organizar_archivos():
    """Organiza los archivos subidos en carpetas según su tipo"""
    if 'archivos' not in request.files:
        return jsonify({'error': 'No se recibieron archivos'}), 400
    
    archivos = request.files.getlist('archivos')
    if not archivos or all(archivo.filename == '' for archivo in archivos):
        return jsonify({'error': 'No se seleccionaron archivos válidos'}), 400
    
    archivos_organizados = []
    
    for archivo in archivo:
        if archivo.filename == '':
            continue
        
        # Generar nombre único para evitar sobrescritura
        nombre_original = archivo.filename
        nombre_base, extension = os.path.splitext(nombre_original)
        nombre_unico = f"{nombre_base}_{uuid.uuid4().hex[:8]}{extension}"
        
        # Determinar tipo de archivo y carpeta destino
        tipo = determinar_tipo_archivo(nombre_original)
        carpeta_destino = os.path.join(app.config['UPLOAD_FOLDER'], tipo)
        
        # Crear carpeta si no existe
        os.makedirs(carpeta_destino, exist_ok=True)
        
        # Guardar archivo
        ruta_destino = os.path.join(carpeta_destino, secure_filename(nombre_unico))
        archivo.save(ruta_destino)
        
        archivos_organizados.append({
            'nombre_original': nombre_original,
            'nombre_guardado': nombre_unico,
            'tipo': tipo,
            'ruta': ruta_destino
        })
    
    return jsonify({
        'mensaje': f'Se organizaron {len(archivos_organizados)} archivos',
        'archivos': archivos_organizados
    })

def determinar_tipo_archivo(nombre_archivo):
    """Determina el tipo de archivo según su extensión"""
    extension = os.path.splitext(nombre_archivo)[1].lower()
    
    tipos = {
        'documentos': ['.txt', '.doc', '.docx', '.pdf', '.odt', '.rtf'],
        'imagenes': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
        'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
        'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'],
        'comprimidos': ['.zip', '.rar', '.7z', '.tar', '.gz']
    }
    
    for tipo, extensiones in tipos.items():
        if extension in extensiones:
            return tipo.capitalize()
    
    return 'Otros'

@app.route('/ver-carpetas')
def ver_carpetas():
    """Muestra la estructura de carpetas creadas"""
    base_path = Path(app.config['UPLOAD_FOLDER'])
    estructura = {}
    
    if base_path.exists():
        for carpeta in base_path.iterdir():
            if carpeta.is_dir():
                archivos = [f.name for f in carpeta.iterdir() if f.is_file()]
                estructura[carpeta.name] = archivos
    
    return jsonify(estructura)

@app.route('/descargar-organizado')
def descargar_organizado():
    """Descarga un ZIP con todos los archivos organizados"""
    base_path = Path(app.config['UPLOAD_FOLDER'])
    
    if not base_path.exists() or not any(base_path.iterdir()):
        return jsonify({'error': 'No hay archivos organizados aún'}), 404
    
    # Crear ZIP en memoria
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for carpeta in base_path.iterdir():
            if carpeta.is_dir():
                for archivo in carpeta.iterdir():
                    if archivo.is_file():
                        # Agregar al ZIP manteniendo la estructura de carpetas
                        arcname = f"{carpeta.name}/{archivo.name}"
                        zf.write(archivo, arcname)
    
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='archivos_organizados.zip'
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
