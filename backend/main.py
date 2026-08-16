from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from io import BytesIO
import os
import httpx

# ========================================
# Load Environment Variables
# ========================================

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


# ========================================
# FastAPI
# ========================================

app = FastAPI()


# ========================================
# CORS
# ========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hedayaodat20-cell.github.io"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# Home
# ========================================

@app.get("/")
def home():

    return {
        "status": "online",
        "message": "Voice Clone AI backend is running"
    }


# ========================================
# Generate Voice
# ========================================

@app.post("/generate")
async def generate_voice(
    file: UploadFile = File(...),
    text: str = Form(...)
):

    # ------------------------------------
    # Check API Key
    # ------------------------------------

    if not ELEVENLABS_API_KEY:

        raise HTTPException(
            status_code=500,
            detail="ElevenLabs API key is not configured."
        )


    # ------------------------------------
    # Check Text
    # ------------------------------------

    text = text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Please enter some text."
        )


    # ------------------------------------
    # Check Audio File
    # ------------------------------------

    allowed_extensions = (
        ".mp3",
        ".wav",
        ".m4a",
        ".webm",
        ".mpeg",
        ".mpga"
    )

    filename = (file.filename or "").lower()

    if not filename.endswith(allowed_extensions):

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. "
                "Please upload MP3, WAV, M4A, or WEBM."
            )
        )


    # ------------------------------------
    # Read Audio
    # ------------------------------------

    audio_data = await file.read()

    if not audio_data:

        raise HTTPException(
            status_code=400,
            detail="The audio file is empty."
        )


    # ====================================
    # STEP 1
    # Create Instant Voice Clone
    # ====================================

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
            file.content_type or "application/octet-stream"
        )
    }


    try:

        async with httpx.AsyncClient(
            timeout=120
        ) as client:

            clone_response = await client.post(
                f"{ELEVENLABS_BASE_URL}/voices/add",
                headers=headers,
                data=clone_data,
                files=files
            )

    except Exception as error:

        print("Clone connection error:", error)

        raise HTTPException(
            status_code=502,
            detail="Could not connect to the voice cloning service."
        )


    # ------------------------------------
    # Handle Clone Error
    # ------------------------------------

    if clone_response.status_code != 200:

        print(
            "ElevenLabs clone error:",
            clone_response.status_code,
            clone_response.text
        )

        try:
            error_data = clone_response.json()

            detail = (
                error_data
                .get("detail", {})
                .get("message")
            )

        except Exception:

            detail = None


        raise HTTPException(
            status_code=502,
            detail=detail or "Could not create the voice clone."
        )


    # ------------------------------------
    # Get Voice ID
    # ------------------------------------

    clone_result = clone_response.json()

    voice_id = clone_result.get("voice_id")

    if not voice_id:

        raise HTTPException(
            status_code=500,
            detail="Voice ID was not returned."
        )


    # ====================================
    # STEP 2
    # Generate Speech
    # ====================================

    tts_headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    tts_data = {
        "text": text,
        "model_id": "eleven_multilingual_v2"
    }


    try:

        async with httpx.AsyncClient(
            timeout=120
        ) as client:

            audio_response = await client.post(
                f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}",
                params={
                    "output_format": "mp3_44100_128"
                },
                headers=tts_headers,
                json=tts_data
            )

    except Exception as error:

        print("TTS connection error:", error)

        raise HTTPException(
            status_code=502,
            detail="Could not connect to the speech generation service."
        )


    # ------------------------------------
    # Handle TTS Error
    # ------------------------------------

    if audio_response.status_code != 200:

        print(
            "ElevenLabs TTS error:",
            audio_response.status_code,
            audio_response.text
        )

        raise HTTPException(
            status_code=502,
            detail="Could not generate the voice."
        )


    # ====================================
    # Return Generated Audio
    # ====================================

    return StreamingResponse(
        BytesIO(audio_response.content),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition":
            'inline; filename="voice-clone.mp3"'
        }
    )
