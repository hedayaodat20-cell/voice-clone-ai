from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from TTS.api import TTS
import tempfile
import os
import torch
import torchaudio

app = FastAPI()

# تحميل XTTS-v2
print("Loading XTTS-v2...")

device = "cuda" if torch.cuda.is_available() else "cpu"

os.environ["COQUI_TOS_AGREED"] = "1"

tts = TTS(
    "tts_models/multilingual/multi-dataset/xtts_v2",
    progress_bar=False
).to(device)

print("XTTS-v2 loaded successfully!")


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>Voice Clone AI</title>

        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 40px auto;
                padding: 20px;
                background: #f7f7f7;
            }

            .box {
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0,0,0,.08);
            }

            input, textarea, button {
                width: 100%;
                box-sizing: border-box;
                margin-top: 12px;
                padding: 13px;
                font-size: 16px;
            }

            button {
                cursor: pointer;
                background: #222;
                color: white;
                border: 0;
                border-radius: 8px;
            }

            button:disabled {
                opacity: .6;
            }

            audio {
                width: 100%;
                margin-top: 20px;
            }

            #status {
                margin-top: 15px;
                font-weight: bold;
            }
        </style>
    </head>

    <body>

        <div class="box">

            <h1>🎙️ Voice Clone AI</h1>

            <p>
                ارفعي تسجيل صوتي، ثم اكتبي النص الذي تريدين تحويله إلى صوت.
            </p>

            <input
                id="file"
                type="file"
                accept="audio/*"
            >

            <textarea
                id="text"
                rows="5"
                placeholder="اكتبي النص هنا..."
            ></textarea>

            <button id="button" onclick="generate()">
                توليد الصوت
            </button>

            <div id="status"></div>

            <audio id="audio" controls></audio>

        </div>

        <script>

        async function generate() {

            const file =
                document.getElementById("file").files[0];

            const text =
                document.getElementById("text").value;

            const status =
                document.getElementById("status");

            const audio =
                document.getElementById("audio");

            const button =
                document.getElementById("button");


            if (!file) {
                status.innerText =
                    "❌ اختاري ملف صوتي أولاً";
                return;
            }


            if (!text.trim()) {
                status.innerText =
                    "❌ اكتبي النص أولاً";
                return;
            }


            button.disabled = true;

            status.innerText =
                "⏳ جاري توليد الصوت... قد يستغرق بعض الوقت";


            audio.removeAttribute("src");


            const form = new FormData();

            form.append("file", file);
            form.append("text", text);


            try {

                const response = await fetch(
                    "/generate",
                    {
                        method: "POST",
                        body: form
                    }
                );


                if (!response.ok) {

                    const error =
                        await response.text();

                    throw new Error(error);
                }


                const blob =
                    await response.blob();

                const url =
                    URL.createObjectURL(blob);


                audio.src = url;

                audio.load();


                status.innerText =
                    "✅ تم توليد الصوت — اضغطي تشغيل ▶️";

            }

            catch (error) {

                status.innerText =
                    "❌ حدث خطأ: " + error.message;

            }

            finally {

                button.disabled = false;

            }
        }

        </script>

    </body>
    </html>
    """


@app.post("/generate")
async def generate(
    file: UploadFile = File(...),
    text: str = Form(...)
):

    input_path = None
    output_path = None

    try:

        # ملف الصوت المرجعي
        audio_data = await file.read()

        suffix = os.path.splitext(
            file.filename or ".wav"
        )[1]

        if not suffix:
            suffix = ".wav"


        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as f:

            f.write(audio_data)

            input_path = f.name


        # ملف الصوت الناتج
        output_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        )

        output_path = output_file.name

        output_file.close()


        # XTTS-v2
        tts.tts_to_file(
            text=text,
            speaker_wav=input_path,
            language="ar",
            file_path=output_path
        )


        with open(output_path, "rb") as f:

            result = f.read()


        return Response(
            content=result,
            media_type="audio/wav",
            headers={
                "Content-Disposition":
                'inline; filename="generated_voice.wav"'
            }
        )


    except Exception as e:

        return Response(
            content=f"XTTS error: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )


    finally:

        if input_path and os.path.exists(input_path):
            os.remove(input_path)

        if output_path and os.path.exists(output_path):
            os.remove(output_path)


@app.get("/health")
async def health():

    return {
        "status": "online",
        "service": "Voice Clone AI",
        "model": "XTTS-v2",
        "language": "ar"
    }
