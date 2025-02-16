from flask import Flask, request, jsonify, send_file, render_template
import os
import qrcode
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # Make sure index.html exists in the "templates" folder

UPLOAD_FOLDER = 'static/uploads'
MODEL_FOLDER = 'static/models'
QR_FOLDER = 'static/qrcodes'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MODEL_FOLDER'] = MODEL_FOLDER

models_db = {}  # Store model/image URLs

# ✅ QR Code Generator
def generate_qr(url, filename):
    qr = qrcode.make(url)
    qr_path = os.path.join(QR_FOLDER, filename)
    qr.save(qr_path)
    return filename  # Return just the filename

# ✅ Upload 3D Model or Image
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    filename = secure_filename(file.filename)
    ext = filename.split('.')[-1].lower()
    
    # Decide file type
    if ext in ['glb', 'gltf']:
        folder = MODEL_FOLDER  # 3D Model
        view_type = '3d'
    elif ext in ['jpg', 'jpeg', 'png']:
        folder = UPLOAD_FOLDER  # Image
        view_type = 'image'
    else:
        return jsonify({'error': 'Invalid file type'}), 400

    file_path = os.path.join(folder, filename)
    file.save(file_path)

    # Store URL
    file_url = f'http://127.0.0.1:5000/{folder}/{filename}'
    models_db[filename] = {'url': file_url, 'type': view_type}

    # ✅ Generate QR Code linking to viewer page
    qr_filename = f'qr_{filename}.png'
    qr_path = generate_qr(f'http://127.0.0.1:5000/viewer/{filename}', qr_filename)

    return jsonify({
        'message': 'File uploaded successfully',
        'file_url': file_url,
        'qr_code': f'http://127.0.0.1:5000/{QR_FOLDER}/{qr_filename}',
        'viewer_url': f'http://127.0.0.1:5000/viewer/{filename}'
    })

# ✅ Viewer Page (Handles AR for Models & Images)
@app.route('/viewer/<filename>')
def view_model(filename):
    if filename not in models_db:
        return "File not found", 404

    file_info = models_db[filename]
    return render_template('viewer.html', file_url=file_info['url'], file_type=file_info['type'])

# ✅ Serve Uploaded Files
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route('/static/models/<filename>')
def model_file(filename):
    return send_file(os.path.join(MODEL_FOLDER, filename))

@app.route('/static/qrcodes/<filename>')
def qr_file(filename):
    return send_file(os.path.join(QR_FOLDER, filename))

if __name__ == '__main__':
    app.run(debug=True)
