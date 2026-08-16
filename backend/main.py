from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from io import BytesIO
import os
import httpx

load_dotenv()

app = FastAPI()

# ===============================
# CORS
# ===============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hedayaodat20-cell.github.io"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# Configuration
# ===============================

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    print("WARNING: ELEVENLABS_API_KEY is not configured.")


ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


# ===============================
# Home
# ===============================

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Voice Clone AI backend is running"
    }


# ===============================
# Generate Voice
# ===============================

@app.post("/generate")
async def generate_voice(
    file: UploadFile = File(...),
    text: str = Form(...)
):

    # ---------------------------
    # Check API key
    # ---------------------------

    if not ELEVENLABS_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="ElevenLabs API key is not configured."
        )

    # ---------------------------
    # Check text
    # ---------------------------

    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text is required."
        )

    # ---------------------------
    # Check audio
    # ---------------------------

    allowed_types = [
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/mp4",
        "audio/x-m4a",
        "audio/webm"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid audio file."
        )

    audio_data = await file.read()

    if not audio_data:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty."
        )

    # ===========================
    # STEP 1
    # Create Instant Voice Clone
    # ===========================

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }

    clone_data = {
        "name": "My Voice Clone"
    }

    files = {
        "files": (
            file.filename,
            audio_data,
            file.content_type
        )
    }

    async with httpx.AsyncClient(timeout=120) as client:

        clone_response = await client.post(
            f"{ELEVENLABS_BASE_URL}/voices/add",
            headers=headers,
            data=clone_data,
            files=files
        )

    if clone_response.status_code != 200:

        print(
            "Voice clone error:",
            clone_response.text
        )

        raise HTTPException(
            status_code=clone_response.status_code,
            detail="Could not create the voice clone."
        )

    clone_result = clone_response.json()

    voice_id = clone_result.get("voice_id")

    if not voice_id:
        raise HTTPException(
            status_code=500,
            detail="Voice ID was not returned."
        )

    # ===========================
    # STEP 2
    # Generate Speech
    # ===========================

    tts_headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    tts_data = {
        "text": text,
        "model_id": "eleven_multilingual_v2"
    }

    async with httpx.AsyncClient(timeout=120) as client:

        audio_response = await client.post(
            f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}",
            params={
                "output_format": "mp3_44100_128"
            },
            headers=tts_headers,
            json=tts_data
        )

    if audio_response.status_code != 200:

        print(
            "TTS error:",
            audio_response.text
        )

        raise HTTPException(
            status_code=audio_response.status_code,
            detail="Could not generate the voice."
        )

    # ===========================
    # Return MP3
    # ===========================

    return StreamingResponse(
        BytesIO(audio_response.content),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'inline; filename="voice-clone.mp3"'
        }
    )
