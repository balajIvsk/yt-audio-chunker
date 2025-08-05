from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tempfile, os, subprocess, base64
import requests

app = FastAPI()

class AudioSplitRequest(BaseModel):
    audio_url: str
    chunk_duration: int = 120

@app.post("/split-audio")
async def split_audio(req: AudioSplitRequest):
    logs = []

    try:
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, "input.mp3")

        logs.append(f"📥 Downloading MP3 from {req.audio_url}")
        response = requests.get(req.audio_url, stream=True)

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

        with open(input_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        size = os.path.getsize(input_path)
        logs.append(f"✅ MP3 downloaded — size: {size} bytes")
    except Exception as e:
        logs.append(f"❌ Error downloading file: {str(e)}")
        return {"chunks": [], "logs": logs}

    try:
        output_template = os.path.join(tmp_dir, "chunk_%03d.mp3")
        cmd = [
            "ffmpeg", "-i", input_path, "-f", "segment",
            "-segment_time", str(req.chunk_duration),
            "-c", "libmp3lame", output_template
        ]
        logs.append("🛠️ Running ffmpeg command:")
        logs.append(" ".join(cmd))

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stderr_output = result.stderr.decode()
        logs.append("🪵 FFMPEG STDERR:")
        logs.append(stderr_output)

        chunk_files = sorted([f for f in os.listdir(tmp_dir) if f.startswith("chunk_")])
        logs.append(f"🔍 Found {len(chunk_files)} chunk(s)")

        output = []
        for chunk in chunk_files:
            chunk_path = os.path.join(tmp_dir, chunk)
            with open(chunk_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                output.append({ "filename": chunk, "base64": b64 })

        logs.append("✅ Chunking complete")
        return { "chunks": output, "logs": logs }

    except Exception as e:
        logs.append(f"❌ Error during ffmpeg split: {str(e)}")
        return {"chunks": [], "logs": logs}
