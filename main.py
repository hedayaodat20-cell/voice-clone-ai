from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    StreamingResponse,
    HTMLResponse,
)
from gradio_client import Client, handle_file
from io import BytesIO
import os
import tempfile
import traceback
import base64


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
        print(
            "Connecting to Hugging Face XTTS Space...",
            flush=True
        )

        client = Client(SPACE_ID)

        print(
            "Connected to Hugging Face XTTS Space.",
            flush=True
        )

    return client


# =========================================================
# HOME PAGE
# =========================================================

@app.get("/", response_class=HTMLResponse)
async def home():

    return """
<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Voice Clone AI</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Arial,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #111827,
            #1f2937
        );

    min-height: 100vh;

    display: flex;

    justify-content: center;

    align-items: center;

    padding: 20px;

    color: white;
}

.container {

    width: 100%;

    max-width: 600px;

    background: #ffffff;

    color: #111827;

    border-radius: 24px;

    padding: 30px;

    box-shadow:
        0 20px 60px
        rgba(0,0,0,0.35);
}

h1 {

    text-align: center;

    margin-top: 0;

    font-size: 32px;
}

.subtitle {

    text-align: center;

    color: #6b7280;

    margin-bottom: 30px;
}

label {

    display: block;

    font-weight: bold;

    margin-bottom: 8px;
}

input[type="file"] {

    width: 100%;

    padding: 12px;

    border: 1px solid #d1d5db;

    border-radius: 12px;

    margin-bottom: 20px;
}

textarea {

    width: 100%;

    min-height: 130px;

    resize: vertical;

    padding: 14px;

    border: 1px solid #d1d5db;

    border-radius: 12px;

    font-size: 17px;

    font-family: inherit;

    margin-bottom: 20px;
}

button {

    width: 100%;

    border: none;

    border-radius: 12px;

    padding: 15px;

    background: #111827;

    color: white;

    font-size: 18px;

    font-weight: bold;

    cursor: pointer;
}

button:hover {

    background: #374151;
}

button:disabled {

    opacity: 0.6;

    cursor: not-allowed;
}

.status {

    text-align: center;

    margin-top: 20px;

    min-height: 25px;

    color: #6b7280;
}

.audio-box {

    display: none;

    margin-top: 25px;

    padding: 20px;

    background: #f3f4f6;

    border-radius: 16px;
}

.audio-box h3 {

    margin-top: 0;

    text-align: center;
}

audio {

    width: 100%;

    margin-top: 10px;
}

.download {

    display: block;

    text-align: center;

    margin-top: 15px;

    text-decoration: none;

    color: #111827;

    font-weight: bold;
}

.error {

    color: #dc2626;
}

.success {

    color: #16a34a;
}

</style>

</head>


<body>


<div class="container">

    <h1>🎙️ Voice Clone AI</h1>

    <div class="subtitle">
        استنسخ صوتك وحوّل النص العربي إلى صوت
    </div>


    <label>
        التسجيل الصوتي
    </label>

    <input
        id="voiceFile"
        type="file"
        accept="audio/*"
    >


    <label>
        النص
    </label>

    <textarea
        id="text"
        placeholder="اكتب النص الذي تريد تحويله إلى صوت..."
    >مرحبا، هذا اختبار للصوت العربي.</textarea>


    <button
        id="generateButton"
        onclick="generateVoice()"
    >
        🎤 توليد الصوت
    </button>


    <div
        id="status"
        class="status"
    ></div>


    <div
        id="audioBox"
        class="audio-box"
    >

        <h3>
            🔊 الصوت الناتج
        </h3>

        <audio
            id="audioPlayer"
            controls
        ></audio>

        <a
            id="downloadLink"
            class="download"
            download="generated_voice.wav"
        >
            ⬇️ تنزيل الصوت
        </a>

    </div>

</div>


<script>

async function generateVoice() {

    const fileInput =
        document.getElementById("voiceFile");

    const textInput =
        document.getElementById("text");

    const button =
        document.getElementById("generateButton");

    const status =
        document.getElementById("status");

    const audioBox =
        document.getElementById("audioBox");

    const audioPlayer =
        document.getElementById("audioPlayer");

    const downloadLink =
        document.getElementById("downloadLink");


    if (!fileInput.files.length) {

        status.className =
            "status error";

        status.textContent =
            "يرجى اختيار ملف صوتي أولاً.";

        return;
    }


    if (!textInput.value.trim()) {

        status.className =
            "status error";

        status.textContent =
            "يرجى كتابة النص.";

        return;
    }


    const formData =
        new FormData();


    formData.append(
        "file",
        fileInput.files[0]
    );


    formData.append(
        "text",
        textInput.value
    );


    button.disabled = true;

    button.textContent =
        "⏳ جاري توليد الصوت...";


    status.className =
        "status";

    status.textContent =
        "جاري الاتصال بـ XTTS، انتظر قليلاً...";


    audioBox.style.display =
        "none";


    try {

        const response =
            await fetch(
                "/generate",
                {
                    method: "POST",
                    body: formData
                }
            );


        if (!response.ok) {

            let message =
                "حدث خطأ أثناء توليد الصوت.";

            try {

                const error =
                    await response.json();

                if (error.detail) {

                    message =
                        error.detail;
                }

            } catch (_) {}

            throw new Error(message);
        }


        const audioBlob =
            await response.blob();


        if (!audioBlob.size) {

            throw new Error(
                "تم استلام ملف صوتي فارغ."
            );
        }


        const audioUrl =
            URL.createObjectURL(
                audioBlob
            );


        audioPlayer.src =
            audioUrl;


        downloadLink.href =
            audioUrl;


        audioBox.style.display =
            "block";


        status.className =
            "status success";

        status.textContent =
            "✅ تم توليد الصوت بنجاح!";


        audioPlayer.play().catch(
            () => {}
        );

    }

    catch (error) {

        console.error(error);

        status.className =
            "status error";

        status.textContent =
            "❌ " + error.message;
    }


    finally {

        button.disabled = false;

        button.textContent =
            "🎤 توليد الصوت";
    }

}

</script>


</body>

</html>
"""


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

@app.post(
    "/generate",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {
                "audio/wav": {}
            },
            "description": "Generated voice audio"
        }
    }
)
async def generate(
    file: UploadFile = File(...),
    text: str = Form(...)
):

    print(
        "\n========================================",
        flush=True
    )

    print(
        "XTTS REQUEST",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )

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


    if not text.strip():

        raise HTTPException(
            status_code=400,
            detail="Text is empty."
        )


    voice_path = None


    try:

        # =================================================
        # SAVE VOICE
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

            content =
                await file.read()

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
            os.path.getsize(voice_path),
            "bytes",
            flush=True
        )


        # =================================================
        # CONNECT TO HUGGING FACE
        # =================================================

        hf_client =
            get_client()


        # =================================================
        # XTTS
        # =================================================

        print(
            "Calling XTTS...",
            flush=True
        )


        result = hf_client.predict(
            text=text,
            speaker_wav=handle_file(
                voice_path
            ),
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
        # FIND AUDIO
        # =================================================

        audio_path = None


        if isinstance(result, str):

            audio_path = result


        elif isinstance(
            result,
            (list, tuple)
        ):

            for item in result:

                if isinstance(
                    item,
                    str
                ):

                    lower =
                        item.lower()


                    if (
                        lower.endswith(".wav")
                        or
                        lower.endswith(".mp3")
                        or
                        lower.endswith(".flac")
                        or
                        lower.endswith(".ogg")
                    ):

                        audio_path =
                            item

                        break


                elif isinstance(
                    item,
                    dict
                ):

                    possible = (
                        item.get("path")
                        or
                        item.get("url")
                        or
                        item.get("name")
                    )


                    if possible:

                        audio_path =
                            possible

                        break


        elif isinstance(
            result,
            dict
        ):

            audio_path = (
                result.get("path")
                or
                result.get("url")
                or
                result.get("name")
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
        # CHECK FILE
        # =================================================

        if not os.path.exists(
            audio_path
        ):

            raise RuntimeError(
                "XTTS returned a path "
                "that does not exist: "
                f"{audio_path}"
            )


        # =================================================
        # READ AUDIO
        # =================================================

        with open(
            audio_path,
            "rb"
        ) as audio_file:

            audio_data =
                audio_file.read()


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
                    'inline; filename="generated_voice.wav"',

                "Content-Length":
                    str(len(audio_data))
            }
        )


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


    finally:

        try:

            if (
                voice_path
                and
                os.path.exists(
                    voice_path
                )
            ):

                os.remove(
                    voice_path
                )

        except Exception:

            pass
