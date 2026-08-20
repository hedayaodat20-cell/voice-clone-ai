from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from TTS.api import TTS

from io import BytesIO
import os
import tempfile
import traceback


# =========================================================
# APP
# =========================================================

app = FastAPI(title="Voice Clone AI")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# XTTS-V2
# =========================================================

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"

tts = None


def get_tts():
    global tts

    if tts is None:
        print("========================================")
        print("Loading XTTS-v2...")
        print("========================================")

        tts = TTS(
            model_name=MODEL_NAME,
            progress_bar=False,
            gpu=False
        )

        print("XTTS-v2 loaded successfully.")

    return tts


# =========================================================
# HOME
# =========================================================

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "Voice Clone AI",
        "model": MODEL_NAME
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": tts is not None
    }


# =========================================================
# GENERATE
# =========================================================

@app.post("/generate")
async def generate(
    file: UploadFile = File(...),
    text: str = Form(...)
):

    print("\n========================================")
    print("XTTS REQUEST")
    print("========================================")

    print("Filename:", file.filename)
    print("Content type:", file.content_type)
    print("Text:", text)

    # -----------------------------------------------------
    # Validate text
    # -----------------------------------------------------

    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text is empty."
        )

    # -----------------------------------------------------
    # Validate file
    # -----------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No audio filename was provided."
        )

    voice_path = None
    output_path = None

    try:

        # =================================================
        # SAVE VOICE SAMPLE
        # =================================================

        suffix = os.path.splitext(
            file.filename
        )[1].lower()

        allowed_extensions = {
            ".wav",
            ".mp3",
            ".m4a",
            ".flac",
            ".ogg"
        }

        if suffix not in allowed_extensions:
            suffix = ".wav"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_voice:

            voice_path = temp_voice.name

            content = await file.read()

            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded audio file is empty."
                )

            temp_voice.write(content)

        print("Voice saved:", voice_path)
        print(
            "Voice size:",
            os.path.getsize(voice_path),
            "bytes"
        )

        # =================================================
        # LOAD XTTS
        # =================================================

        model = get_tts()

        # =================================================
        # OUTPUT FILE
        # =================================================

        output_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        )

        output_path = output_file.name

        output_file.close()

        print("Output path:", output_path)

        # =================================================
        # GENERATE
        # =================================================

        print("Generating Arabic voice...")

        model.tts_to_file(
            text=text,
            speaker_wav=voice_path,
            language="ar",
            file_path=output_path
        )

        print("XTTS generation finished.")

        # =================================================
        # CHECK OUTPUT
        # =================================================

        if not os.path.exists(output_path):
            raise RuntimeError(
                "XTTS did not create an output audio file."
            )

        audio_size = os.path.getsize(output_path)

        if audio_size == 0:
            raise RuntimeError(
                "XTTS created an empty audio file."
            )

        print(
            "Audio generated successfully:",
            audio_size,
            "bytes"
        )

        # =================================================
        # READ AUDIO
        # =================================================

        with open(output_path, "rb") as audio_file:
            audio_data = audio_file.read()

        if not audio_data:
            raise RuntimeError(
                "Generated audio data is empty."
            )

        # =================================================
        # RETURN AUDIO
        # =================================================

        return StreamingResponse(
            BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition":
                    'inline; filename="generated_voice.wav"',
                "Content-Length":
                    str(len(audio_data))
            }
        )

    except HTTPException:
        raise

    except Exception as e:

        print("\n========================================")
        print("XTTS ERROR")
        print("========================================")

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"XTTS generation failed: {str(e)}"
        )

    finally:

        # =================================================
        # CLEAN TEMP FILES
        # =================================================

        try:

            if voice_path and os.path.exists(voice_path):
                os.remove(voice_path)

        except Exception:
            pass

        try:

            if output_path and os.path.exists(output_path):
                os.remove(output_path)

        except Exception:
            pass
