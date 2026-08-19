```python
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
# Find audio file
# ========================================

def find_audio_file(result):

    # ------------------------------------
    # String
    # ------------------------------------

    if isinstance(result, str):

        if os.path.isfile(result):
            return result

        return None


    # ------------------------------------
    # List / Tuple
    # ------------------------------------

    if isinstance(result, (list, tuple)):

        for item in result:

            found = find_audio_file(item)

            if found:
                return found

        return None


    # ------------------------------------
    # Dictionary
    # ------------------------------------

    if isinstance(result, dict):

        for value in result.values():

            found = find_audio_file(value)

            if found:
                return found

        return None


    # ------------------------------------
    # Gradio FileData / object
    # ------------------------------------

    if hasattr(result, "path"):

        path = getattr(
            result,
            "path",
            None
        )

        if path and os.path.isfile(path):
            return path


    return None


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
    # Read audio
    # ====================================

    audio_data = await file.read()


    if not audio_data:

        raise HTTPException(
            status_code=400,
            detail="The uploaded audio file is empty."
        )


    print("================================")
    print("INPUT FILE:", file.filename)
    print("CONTENT TYPE:", file.content_type)
    print("AUDIO SIZE:", len(audio_data))
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


        print(
            "TEMP AUDIO:",
            temp_path
        )


        # ====================================
        # Connect to Hugging Face
        # ====================================

        print(
            "Connecting to:",
            HF_SPACE
        )


        if HF_TOKEN:

            client = Client(
                HF_SPACE,
                hf_token=HF_TOKEN
            )

        else:

            client = Client(
                HF_SPACE
            )


        print(
            "Connected to Hugging Face."
        )


        # ====================================
        # Generate voice
        # ====================================

        print(
            "Sending request to XTTS..."
        )


        result = client.predict(

            text,

            handle_file(
                temp_path
            ),

            "ar",

            api_name="/predict"

        )


        # ====================================
        # DEBUG RESULT
        # ====================================

        print(
            "================================"
        )

        print(
            "XTTS RAW RESULT:"
        )

        print(
            repr(result)
        )

        print(
            "RESULT TYPE:",
            type(result)
        )

        print(
            "================================"
        )


        # ====================================
        # Find output audio
        # ====================================

        output_path = find_audio_file(
            result
        )


        # ====================================
        # No audio
        # ====================================

        if not output_path:

            raise HTTPException(

                status_code=502,

                detail=(
                    "XTTS did not return an audio file. "
                    "Check Render logs for XTTS RAW RESULT."
                )

            )


        print(
            "OUTPUT AUDIO:",
            output_path
        )


        # ====================================
        # Read generated audio
        # ====================================

        with open(
            output_path,
            "rb"
        ) as audio_file:

            generated_audio = (
                audio_file.read()
            )


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
        # Return WAV
        # ====================================

        return StreamingResponse(

            BytesIO(
                generated_audio
            ),

            media_type="audio/wav",

            headers={
                "Content-Disposition":
                'inline; filename="voice-clone.wav"'
            }

        )


    except HTTPException:

        raise


    except Exception as error:

        print(
            "================================"
        )

        print(
            "XTTS ERROR:"
        )

        print(
            repr(error)
        )

        print(
            "================================"
        )


        raise HTTPException(

            status_code=502,

            detail=(
                "Voice generation failed: "
                + str(error)
            )

        )


    finally:

        # ====================================
        # Delete temporary input
        # ====================================

        if temp_path:

            try:

                if os.path.exists(
                    temp_path
                ):

                    os.remove(
                        temp_path
                    )

            except Exception:

                pass
```
