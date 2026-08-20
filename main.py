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
# HUGGING FACE XTTS SPACE
# =========================================================

SPACE_ID = "applore/xtts-voice-cloning-demo"

client = None


def get_client():
    global client

    if client is None:
        print("Connecting to Hugging Face XTTS Space...", flush=True)

        client = Client(SPACE_ID)

        print(
            "Connected to Hugging Face XTTS Space.",
            flush=True
        )

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

    print("\n========================================", flush=True)
    print("XTTS REQUEST", flush=True)
    print("========================================", flush=True)

    print(
        "Filename:",
        file.filename,
        flush=True
    )

    print(
        "Content type:",
        file.content_type,
        flush=True
    )

    print(
        "Text:",
        text,
        flush=True
    )


    # =====================================================
    # VALIDATE TEXT
    # =====================================================

    if not text or not text.strip():

        raise HTTPException(
            status_code=400,
            detail="Text is empty."
        )


    # =====================================================
    # VALIDATE FILE
    # =====================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Audio file is missing."
        )


    voice_path = None


    try:

        # =================================================
        # SAVE UPLOADED VOICE
        # =================================================

        suffix = os.path.splitext(
            file.filename
        )[1].lower()


        if not suffix:

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


        print(
            "Voice saved to:",
            voice_path,
            flush=True
        )

        print(
            "Voice size:",
            len(content),
            "bytes",
            flush=True
        )


        # =================================================
        # CONNECT TO HUGGING FACE
        # =================================================

        hf_client = get_client()


        # =================================================
        # CALL XTTS
        #
        # Arabic = ar
        # =================================================

        print(
            "Calling XTTS...",
            flush=True
        )


        result = hf_client.predict(
            text=text,
            speaker_wav=handle_file(voice_path),
            language="ar",
            api_name="/predict"
        )


        print(
            "========================================",
            flush=True
        )

        print(
            "XTTS RESULT:",
            flush=True
        )

        print(
            repr(result),
            flush=True
        )

        print(
            "========================================",
            flush=True
        )


        # =================================================
        # FIND AUDIO RESULT
        # =================================================

        audio_path = None


        # -------------------------------------------------
        # STRING RESULT
        # -------------------------------------------------

        if isinstance(result, str):

            audio_path = result


        # -------------------------------------------------
        # LIST / TUPLE RESULT
        # -------------------------------------------------

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


        # -------------------------------------------------
        # DICT RESULT
        # -------------------------------------------------

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


        print(
            "Audio path:",
            audio_path,
            flush=True
        )


        # =================================================
        # CHECK AUDIO PATH
        # =================================================

        if not os.path.exists(audio_path):

            raise RuntimeError(
                "XTTS returned an audio path that "
                "does not exist on this server: "
                f"{audio_path}"
            )


        # =================================================
        # READ AUDIO
        # =================================================

        with open(
            audio_path,
            "rb"
        ) as audio_file:

            audio_data = audio_file.read()


        if not audio_data:

            raise RuntimeError(
                "XTTS returned an empty audio file."
            )


        print(
            "Audio generated successfully:",
            len(audio_data),
            "bytes",
            flush=True
        )


        # =================================================
        # RETURN AUDIO
        # =================================================

        return StreamingResponse(
            BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition":
                    'inline; filename="generated_voice.wav"'
            }
        )


    # =====================================================
    # ERRORS
    # =====================================================

    except HTTPException:

        raise


    except Exception as e:

        print(
            "\n========================================",
            flush=True
        )

        print(
            "XTTS ERROR",
            flush=True
        )

        print(
            "========================================",
            flush=True
        )

        traceback.print_exc()


        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


    # =====================================================
    # CLEANUP
    # =====================================================

    finally:

        try:

            if voice_path:

                if os.path.exists(
                    voice_path
                ):

                    os.remove(
                        voice_path
                    )

                    print(
                        "Temporary voice file removed.",
                        flush=True
                    )

        except Exception as cleanup_error:

            print(
                "Cleanup error:",
                cleanup_error,
                flush=True
            )
