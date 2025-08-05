from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tempfile, os, subprocess, base64
import requests

app = FastAPI()

class AudioSplitRequest(BaseModel):
    audio_url: str
    chunk_duration: int = 120  # seconds

@app.post("/split-audio")
async def split_audio(req: AudioSplitRequest):
    try:
        # Create temp folder and download audio
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, "input.mp3")
        response = requests.get(req.audio_url)
        with open(input_path, "wb") as f:
            f.write(response.content)

        file_size = os.path.getsize(input_path)
        print(f"✅ Downloaded MP3 size: {file_size} bytes")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")

    try:
        # Split using ffmpeg (re-encode for compatibility)
        output_template = os.path.join(tmp_dir, "chunk_%03d.mp3")
        cmd = [
            "ffmpeg", "-i", input_path, "-f", "segment",
            "-segment_time", str(req.chunk_duration),
            "-c", "libmp3lame", output_template
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("🛠️ FFMPEG STDERR:", result.stderr.decode())

        # Get output chunks
        chunks = sorted([f for f in os.listdir(tmp_dir) if f.startswith("chunk_")])
        output = []
        for chunk in chunks:
            chunk_path = os.path.join(tmp_dir, chunk)
            with open(chunk_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                output.append({ "filename": chunk, "base64": b64 })

        return { "chunks": output }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FFMPEG split failed: {str(e)}")
