from flask import Flask, request, jsonify, send_from_directory
import os
import ffmpeg
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
CHUNK_FOLDER = 'chunks'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHUNK_FOLDER, exist_ok=True)

@app.route('/split_audio', methods=['POST'])
def split_audio():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio_file provided'}), 400

    audio_file = request.files['audio_file']
    filename = secure_filename(audio_file.filename)
    file_id = str(uuid.uuid4())
    base_name = os.path.splitext(filename)[0]
    upload_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")
    audio_file.save(upload_path)

    output_template = os.path.join(CHUNK_FOLDER, f"{file_id}_{base_name}_%03d.mp3")

    try:
        (
            ffmpeg
            .input(upload_path)
            .output(output_template, f='segment', segment_time=120, c='copy')
            .run(capture_stdout=True, capture_stderr=True)
        )

        chunk_files = [
            f for f in os.listdir(CHUNK_FOLDER)
            if f.startswith(f"{file_id}_{base_name}_") and f.endswith('.mp3')
        ]
        chunk_files.sort()

        chunk_urls = [request.url_root + f"chunks/{chunk}" for chunk in chunk_files]

        return jsonify({
            'message': 'Audio split successfully',
            'chunks': chunk_urls
        }), 200

    except ffmpeg.Error as e:
        return jsonify({'error': f"FFmpeg error: {e.stderr.decode()}"}), 500
    finally:
        os.remove(upload_path)

@app.route('/chunks/<filename>', methods=['GET'])
def serve_chunk(filename):
    return send_from_directory(CHUNK_FOLDER, filename)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "running"}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
