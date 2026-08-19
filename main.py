from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from gradio_client import Client, handle_file

from io import BytesIO
import os
import tempfile


# ========================================
# Hugging Face Space
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
# Find audio path
# ========================================

def find_audio(result):

    print("SEARCHING RESULT:", repr(result))
    print("RESULT TYPE:", type(result))

    # Direct string
    if isinstance(result, str):

        if os.path.isfile(result):
            return result

        return None

    # List / tuple
    if isinstance(result, (list, tuple)):

        for item in result:

            found = find_audio(item)

            if found:
                return found

        return None

    # Dictionary
    if isinstance(result, dict):

        for value in result.values():

            found = find_audio(value)

            if found:
                return found

        return None

    # Gradio FileData-like object
    if hasattr(result, "path"):

        path = getattr(result, "path", None)

        if path and os.path.isfile(path):
            return path

    return None


# ========================================
# Generate
# ========================================

@app.post("/generate")
async def generate_voice(
    file: UploadFile = File(...),
    text: str = Form(...)
):

    text = text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Please enter some text."
        )


    audio_data = await file.read()


    if not audio_data:

        raise HTTPException(
            status_code=400,
            detail="Uploaded audio file is empty."
        )


    print("================================")
    print("INPUT FILE:", file.filename)
    print("CONTENT TYPE:", file.content_type)
    print("AUDIO SIZE:", len(audio_data))
    print("================================")


    temp_path = None


    try:

        # ====================================
        # Save uploaded audio
        # ====================================

        extension = ".wav"

        if file.filename:

            ext = os.path.splitext(
                file.filename
            )[1]

            if ext:
                extension = ext


        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp:

            temp.write(audio_data)

            temp_path = temp.name


        print(
            "TEMP FILE:",
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
            "Connected successfully."
        )


        # ====================================
        # Discover API
        # ====================================

        api_info = client.view_api(
            all_endpoints=True,
            print_info=True,
            return_format="dict"
        )


        print(
            "================================"
        )

        print(
            "HF API INFO:"
        )

        print(
            api_info
        )

        print(
            "================================"
        )


        # ====================================
        # Find endpoint
        # ====================================

        endpoint = None


        named_endpoints = api_info.get(
            "named_endpoints",
            {}
        )


        if "/predict" in named_endpoints:

            endpoint = "/predict"


        elif named_endpoints:

            endpoint = list(
                named_endpoints.keys()
            )[0]


        # ====================================
        # If no named endpoint
        # ====================================

        if not endpoint:

            unnamed = api_info.get(
                "unnamed_endpoints",
                {}
            )


            if unnamed:

                endpoint_index = list(
                    unnamed.keys()
                )[0]

                print(
                    "Using unnamed endpoint:",
                    endpoint_index
                )


                result = client.predict(

                    text,

                    handle_file(
                        temp_path
                    ),

                    "ar",

                    fn_index=endpoint_index

                )

            else:

                raise HTTPException(
                    status_code=502,
                    detail="No XTTS API endpoint was found."
                )


        else:

            print(
                "Using endpoint:",
                endpoint
            )


            # ====================================
            # Call XTTS
            # ====================================

            result = client.predict(

                text,

                handle_file(
                    temp_path
                ),

                "ar",

                api_name=endpoint

            )


        # ====================================
        # Print result
        # ====================================

        print(
            "================================"
        )

        print(
            "XTTS RESULT:"
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

        output_path = find_audio(
            result
        )


        if not output_path:

            raise HTTPException(

                status_code=502,

                detail=(
                    "XTTS did not return an audio file. "
                    "Check Render logs for XTTS RESULT."
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
        ) as audio:

            generated_audio = audio.read()


        if not generated_audio:

            raise HTTPException(

                status_code=502,

                detail="Generated audio file is empty."

            )


        print(
            "GENERATED AUDIO SIZE:",
            len(generated_audio)
        )


        # ====================================
        # Return audio
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
                "XTTS generation failed: "
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
