from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from gradio_client import Client, handle_file

from io import BytesIO
import os
import shutil
import tempfile


# ========================================
# Environment
# ========================================

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

# Hugging Face XTTS Space
HF_SPACE = "coqui/xtts"


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
        "message": "XTTS Voice Clone backend is running"
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
    # TEXT CHECK
    # ====================================

    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Please enter some text."
        )

    if len(text) > 500:
        raise HTTPException(
            status_code=400,
            detail="Text is too long. Please use less than 500 characters."
        )


    # ====================================
    # FILE CHECK
    # ====================================

    audio_data = await file.read()

    if not audio_data:
        raise HTTPException(
            status_code=400,
            detail="The uploaded audio file is empty."
        )

    print("================================")
    print("FILE NAME:", file.filename)
    print("CONTENT TYPE:", file.content_type)
    print("AUDIO SIZE:", len(audio_data))
    print("================================")


    # ====================================
    # SAVE TEMP AUDIO FILE
    # ====================================

    temp_path = None

    try:

        suffix = ".wav"

        if file.filename:
            original_ext = os.path.splitext(
                file.filename
            )[1]

            if original_ext:
                suffix = original_ext


        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_file.write(audio_data)

            temp_path = temp_file.name


        print("TEMP AUDIO:", temp_path)


        # ====================================
        # CONNECT TO HUGGING FACE
        # ====================================

        print("Connecting to Hugging Face XTTS...")

        if HF_TOKEN:

            client = Client(
                HF_SPACE,
                hf_token=HF_TOKEN
            )

        else:

            client = Client(
                HF_SPACE
            )


        print("Connected to:", HF_SPACE)


        # ====================================
        # SEND TO XTTS
        # ====================================

        print("Sending voice + text to XTTS...")


        result = client.predict(
            text,
            "ar",
            handle_file(temp_path),
            None,
            False,
            False,
            False,
            True,
            api_name="/predict"
        )


        print("XTTS RESULT:", result)


        # ====================================
        # GET GENERATED AUDIO
        # ====================================

        output_file = None


        if isinstance(result, tuple):

            for item in result:

                if isinstance(item, str):

                    if (
                        item.endswith(".wav")
                        or item.endswith(".mp3")
                        or item.endswith(".flac")
                    ):
                        output_file = item
                        break


        elif isinstance(result, str):

            output_file = result


        # ====================================
        # CHECK RESULT
        # ====================================

        if not output_file:

            raise HTTPException(
                status_code=502,
                detail=(
                    "XTTS did not return an audio file."
                )
            )


        if not os.path.exists(output_file):

            raise HTTPException(
                status_code=502,
                detail=(
                    "Generated audio file could not "
                    "be found."
                )
            )


        # ====================================
        # READ GENERATED AUDIO
        # ====================================

        with open(
            output_file,
            "rb"
        ) as audio_file:

            generated_audio = audio_file.read()


        if not generated_audio:

            raise HTTPException(
                status_code=502,
                detail="Generated audio is empty."
            )


        print(
            "GENERATED AUDIO SIZE:",
            len(generated_audio)
        )


        # ====================================
        # RETURN AUDIO
        # ====================================

        return StreamingResponse(
            BytesIO(generated_audio),
            media_type="audio/wav",
            headers={
                "Content-Disposition":
                'inline; filename="voice-clone.wav"'
            }
        )


    except HTTPException:
        raise


    except Exception as error:

        print("================================")
        print("XTTS ERROR:")
        print(error)
        print("================================")

        raise HTTPException(
            status_code=502,
            detail=(
                "Voice generation failed. "
                "Please try again."
            )
        )


    finally:

        # ====================================
        # DELETE TEMP FILE
        # ====================================

        if temp_path and os.path.exists(temp_path):

            try:
                os.remove(temp_path)

            except Exception:
                pass
