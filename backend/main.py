from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from io import BytesIO
import os
import httpx


# ========================================
# Environment
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

    # ====================================
    # API KEY
    # ====================================

    if not ELEVENLABS_API_KEY:

        raise HTTPException(
            status_code=500,
            detail="ElevenLabs API key is not configured."
        )


    # ====================================
    # TEXT
    # ====================================

    text = text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Please enter some text."
        )


    # ====================================
    # FILE INFORMATION
    # ====================================

    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    # Temporary diagnostics
    print("================================")
    print("FILE NAME:", file.filename)
    print("CONTENT TYPE:", file.content_type)
    print("================================")


    # ====================================
    # AUDIO VALIDATION
    # ====================================

    allowed_extensions = (
        ".mp3",
        ".wav",
        ".m4a",
        ".webm",
        ".mpeg",
        ".mpga",
        ".aac",
        ".ogg",
        ".flac"
    )

    is_valid_extension = filename.endswith(
        allowed_extensions
    )

    is_audio_content = content_type.startswith(
        "audio/"
    )


    if not is_valid_extension and not is_audio_content:

        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file was not recognized "
                "as an audio file."
            )
        )


    # ====================================
    # READ AUDIO
    # ====================================

    audio_data = await file.read()

    if not audio_data:

        raise HTTPException(
            status_code=400,
            detail="The audio file is empty."
        )


    print(
        "AUDIO SIZE:",
        len(audio_data),
        "bytes"
    )


    # ====================================
    # STEP 1
    # CREATE INSTANT VOICE CLONE
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

        print(
            "CLONE CONNECTION ERROR:",
            error
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not connect to the "
                "voice cloning service."
            )
        )


    # ====================================
    # CLONE RESPONSE
    # ====================================

    print(
        "CLONE STATUS:",
        clone_response.status_code
    )

    print(
        "CLONE RESPONSE:",
        clone_response.text
    )


    if clone_response.status_code != 200:

        raise HTTPException(
            status_code=502,
            detail=(
                "Voice cloning failed. "
                "Check the Render logs for details."
            )
        )


    # ====================================
    # GET VOICE ID
    # ====================================

    try:

        clone_result = clone_response.json()

    except Exception:

        raise HTTPException(
            status_code=502,
            detail="Invalid response from voice cloning service."
        )


    voice_id = clone_result.get("voice_id")


    if not voice_id:

        raise HTTPException(
            status_code=500,
            detail="Voice ID was not returned."
        )


    print(
        "VOICE ID CREATED:",
        voice_id
    )


    # ====================================
    # STEP 2
    # GENERATE SPEECH
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

        print(
            "TTS CONNECTION ERROR:",
            error
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not connect to the "
                "speech generation service."
            )
        )


    # ====================================
    # TTS RESPONSE
    # ====================================

    print(
        "TTS STATUS:",
        audio_response.status_code
    )


    if audio_response.status_code != 200:

        print(
            "TTS RESPONSE:",
            audio_response.text
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Speech generation failed. "
                "Check the Render logs for details."
            )
        )


    # ====================================
    # RETURN AUDIO
    # ====================================

    return StreamingResponse(
        BytesIO(audio_response.content),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition":
            'inline; filename="voice-clone.mp3"'
        }
    )
