from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess
from werkzeug.utils import secure_filename
import glob

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'chunks'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/split_audio', methods=['POST'])
def split_audio():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio_file provided'}), 400

    audio_file = request.files['audio_file']
    filename = secure_filename(audio_file.filename)
    if filename == '':
        return jsonify({'error': 'No selected file'}), 400

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    audio_file.save(input_path)

    file_basename = os.path.splitext(filename)[0]
    output_pattern = os.path.join(OUTPUT_FOLDER, f"{file_basename}_%03d.mp3")

    try:
        command = [
            'ffmpeg',
            '-i', input_path,
            '-f', 'segment',
            '-segment_time', '120',
            '-c', 'copy',
            output_pattern
        ]
        subprocess.run(command, check=True, capture_output=True)

        # Gather chunk file names
        chunks = sorted(glob.glob(os.path.join(OUTPUT_FOLDER, f"{file_basename}_*.mp3")))
        chunk_urls = [
            request.url_root + f"chunks/{os.path.basename(chunk)}" for chunk in chunks
        ]

        return jsonify({
            'message': 'Audio split successfully',
            'chunks': chunk_urls
        }), 200

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f"FFmpeg failed: {e.stderr.decode()}"}), 500

    finally:
        os.remove(input_path)

@app.route('/chunks/<filename>', methods=['GET'])
def download_chunk(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "running"}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
