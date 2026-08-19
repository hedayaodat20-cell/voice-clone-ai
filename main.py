from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from gradio_client import Client, handle_file
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
# HUGGING FACE SPACE
# =========================================================

SPACE_ID = "applore/xtts-voice-cloning-demo"

client = None


def get_client():
    global client

    if client is None:
        print("Connecting to Hugging Face XTTS Space...")

        client = Client(SPACE_ID)

        print("Connected to Hugging Face XTTS Space.")

    return client


# =========================================================
# HOME
# =========================================================

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "Voice Clone AI",
        "xtts_space": SPACE_ID
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():
    return {
        "status": "ok"
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

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text is empty."
        )

    try:

        # =================================================
        # SAVE UPLOADED VOICE
        # =================================================

        suffix = os.path.splitext(
            file.filename or ".wav"
        )[1]

        if not suffix:
            suffix = ".wav"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_voice:

            voice_path = temp_voice.name

            content = await file.read()

            temp_voice.write(content)

        print("Voice saved to:", voice_path)
        print("Voice size:", os.path.getsize(voice_path))


        # =================================================
        # CONNECT TO SPACE
        # =================================================

        hf_client = get_client()


        # =================================================
        # CALL XTTS
        #
        # The Space's predict function is:
        #
        # predict(text, speaker_wav, language)
        #
        # Arabic = ar
        # =================================================

        print("Calling XTTS...")

        result = hf_client.predict(
            text=text,
            speaker_wav=handle_file(voice_path),
            language="ar",
            api_name="/predict"
        )

        print("========================================")
        print("XTTS RESULT:")
        print(repr(result))
        print("========================================")


        # =================================================
        # FIND AUDIO RESULT
        # =================================================

        audio_path = None

        if isinstance(result, str):

            audio_path = result

        elif isinstance(result, (list, tuple)):

            for item in result:

                if isinstance(item, str):

                    lower = item.lower()

                    if (
                        lower.endswith(".wav")
                        or lower.endswith(".mp3")
                        or lower.endswith(".flac")
                        or lower.endswith(".ogg")
                    ):
                        audio_path = item
                        break


                elif isinstance(item, dict):

                    possible = (
                        item.get("path")
                        or item.get("url")
                        or item.get("name")
                    )

                    if possible:
                        audio_path = possible
                        break


        elif isinstance(result, dict):

            audio_path = (
                result.get("path")
                or result.get("url")
                or result.get("name")
            )


        # =================================================
        # NO AUDIO
        # =================================================

        if not audio_path:

            raise RuntimeError(
                "XTTS did not return an audio file. "
                f"Raw result: {repr(result)}"
            )


        print("Audio path:", audio_path)


        # =================================================
        # READ AUDIO
        # =================================================

        if not os.path.exists(audio_path):

            raise RuntimeError(
                f"XTTS returned a path that does not exist: "
                f"{audio_path}"
            )


        with open(audio_path, "rb") as audio_file:

            audio_data = audio_file.read()


        if not audio_data:

            raise RuntimeError(
                "XTTS returned an empty audio file."
            )


        print(
            "Audio generated successfully:",
            len(audio_data),
            "bytes"
        )


        # =================================================
        # RETURN WAV
        # =================================================

        return StreamingResponse(
            BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition":
                    'inline; filename="generated_voice.wav"'
            }
        )


    except Exception as e:

        print("\n========================================")
        print("XTTS ERROR")
        print("========================================")

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


    finally:

        try:

            if "voice_path" in locals():
                if os.path.exists(voice_path):
                    os.remove(voice_path)

        except Exception:
            pass
