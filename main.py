from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
import httpx
import os

app = FastAPI()

XTTS_SPACE = "https://applore-xtts-voice-cloning-demo.hf.space"


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
            }
            input, textarea, button {
                width: 100%;
                box-sizing: border-box;
                margin-top: 10px;
                padding: 12px;
                font-size: 16px;
            }
            button {
                cursor: pointer;
                background: #222;
                color: white;
                border: 0;
                border-radius: 8px;
            }
            audio {
                width: 100%;
                margin-top: 20px;
            }
            #status {
                margin-top: 15px;
            }
        </style>
    </head>
    <body>

        <h1>🎙️ Voice Clone AI</h1>

        <p>اختاري ملف صوتي ثم اكتبي النص:</p>

        <input id="file" type="file" accept="audio/*">

        <textarea id="text" rows="4"
            placeholder="اكتبي النص الذي تريدين تحويله إلى صوت..."></textarea>

        <button onclick="generate()">توليد الصوت</button>

        <div id="status"></div>

        <audio id="audio" controls></audio>

        <script>
        async function generate() {
            const file = document.getElementById("file").files[0];
            const text = document.getElementById("text").value;
            const status = document.getElementById("status");
            const audio = document.getElementById("audio");

            if (!file) {
                status.innerText = "❌ اختاري ملف صوتي أولاً";
                return;
            }

            if (!text.trim()) {
                status.innerText = "❌ اكتبي النص أولاً";
                return;
            }

            status.innerText = "⏳ جاري توليد الصوت...";
            audio.removeAttribute("src");

            const form = new FormData();
            form.append("file", file);
            form.append("text", text);

            try {
                const response = await fetch("/generate", {
                    method: "POST",
                    body: form
                });

                if (!response.ok) {
                    const error = await response.text();
                    throw new Error(error);
                }

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);

                audio.src = url;
                audio.load();

                status.innerText = "✅ تم توليد الصوت — اضغطي تشغيل ▶️";
            } catch (error) {
                status.innerText = "❌ حدث خطأ: " + error.message;
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
    audio_data = await file.read()

    files = {
        "audio": (
            file.filename,
            audio_data,
            file.content_type or "audio/wav"
        )
    }

    data = {
        "text": text
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            XTTS_SPACE,
            files=files,
            data=data
        )

    if response.status_code != 200:
        return Response(
            content=response.text,
            status_code=response.status_code,
            media_type="text/plain"
        )

    return Response(
        content=response.content,
        media_type="audio/wav",
        headers={
            "Content-Disposition": 'inline; filename="generated_voice.wav"'
        }
    )


@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": "Voice Clone AI"
    }
