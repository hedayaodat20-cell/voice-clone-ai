from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from gradio_client import Client, handle_file

from io import BytesIO
import os
import tempfile


# ========================================
# Configuration
# ========================================

HF_SPACE = "applore/xtts-voice-cloning-demo"

HF_TOKEN = os.getenv("HF_TOKEN")


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
    # Validate text
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
            detail="Text is too long."
        )


    # ====================================
    # Read uploaded audio
    # ====================================

    audio_data = await file.read()

    if not audio_data:
        raise HTTPException(
            status_code=400,
            detail="The uploaded audio file is empty."
        )


    print("================================")
    print("FILE:", file.filename)
    print("TYPE:", file.content_type)
    print("SIZE:", len(audio_data))
    print("================================")


    temp_path = None

    try:

        # ====================================
        # Create temporary audio file
        # ====================================

        extension = ".wav"

        if file.filename:

            original_extension = os.path.splitext(
                file.filename
            )[1]

            if original_extension:
                extension = original_extension


        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            temp_file.write(audio_data)

            temp_path = temp_file.name


        print("TEMP FILE:", temp_path)


        # ====================================
        # Connect to Hugging Face
        # ====================================

        print("Connecting to Hugging Face...")

        if HF_TOKEN:

            client = Client(
                HF_SPACE,
                hf_token=HF_TOKEN
            )

        else:

            client = Client(
                HF_SPACE
            )


        print("Connected successfully.")


        # ====================================
        # Generate cloned voice
        # ====================================

        print("Sending audio + text to XTTS...")


        result = client.predict(
            text,
            handle_file(temp_path),
            "ar",
            api_name="/predict"
        )


        print("XTTS RESULT:")
        print(result)


        # ====================================
        # Find generated audio
        # ====================================

        output_path = None


        if isinstance(result, str):

            output_path = result


        elif isinstance(result, tuple):

            for item in result:

                if isinstance(item, str):

                    lower_item = item.lower()

                    if (
                        lower_item.endswith(".wav")
                        or lower_item.endswith(".mp3")
                        or lower_item.endswith(".flac")
                    ):
                        output_path = item
                        break


        # ====================================
        # Validate output
        # ====================================

        if not output_path:

            raise HTTPException(
                status_code=502,
                detail="XTTS did not return an audio file."
            )


        print("OUTPUT:", output_path)


        if not os.path.exists(output_path):

            raise HTTPException(
                status_code=502,
                detail="Generated audio file was not found."
            )


        # ====================================
        # Read generated audio
        # ====================================

        with open(
            output_path,
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
        # Return audio
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
        # Delete temporary file
        # ====================================

        if temp_path:

            try:

                if os.path.exists(temp_path):
                    os.remove(temp_path)

            except Exception:
                pass
