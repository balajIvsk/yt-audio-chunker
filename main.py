from flask import Flask, request, jsonify
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
    os.makedirs(temp_upload_dir, exist_ok=True)
    os.makedirs(temp_output_dir, exist_ok=True)

    try:
        # Save uploaded file
        filename = audio_file.filename.replace(" ", "_")
        input_path = os.path.join(temp_upload_dir, filename)
        audio_file.save(input_path)
        logs.append(f"📥 Uploaded file saved at: {input_path}")

        # Prepare output file pattern
        output_template = os.path.join(temp_output_dir, f"{filename.split('.')[0]}_%03d.mp3")

        # Run ffmpeg with re-encoding
        command = [
            'ffmpeg',
            '-i', input_path,
            '-f', 'segment',
            '-segment_time', '120',
            '-c:a', 'libmp3lame',
            '-b:a', '128k',
            output_template
        ]
        logs.append(f"🛠️ Running ffmpeg: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        logs.append("🪵 FFMPEG STDOUT:\n" + result.stdout)
        logs.append("🪵 FFMPEG STDERR:\n" + result.stderr)

        # List chunk URLs
        chunk_urls = []
        for filename in sorted(os.listdir(temp_output_dir)):
            if filename.endswith(".mp3"):
                file_url = f"{request.url_root}chunks/{unique_id}/{filename}"
                chunk_urls.append(file_url)

        if not chunk_urls:
            logs.append("⚠️ No audio chunks were created.")

        return jsonify({
            'chunks': chunk_urls,
            'message': 'Audio split successfully',
            'logs': logs
        })

    except Exception as e:
        logs.append(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e), 'logs': logs}), 500

    finally:
        # Keep files for download — don't auto-delete here
        pass


@app.route('/chunks/<folder>/<filename>', methods=['GET'])
def serve_chunk(folder, filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], folder, filename)
    if os.path.exists(file_path):
        return app.send_static_file(file_path)
    return "File not found", 404


if __name__ == '__main__':
    app.run(debug=True)
