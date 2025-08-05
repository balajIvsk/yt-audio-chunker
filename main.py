from flask import Flask, request, jsonify, send_file
import subprocess
import os
import uuid
import shutil

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'chunks'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/split_audio', methods=['POST'])
def split_audio():
    logs = []

    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio_file provided'}), 400

    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Generate unique ID for temp folder
    unique_id = str(uuid.uuid4())
    temp_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
    temp_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], unique_id)
    os.makedirs(temp_upload_dir, exist
