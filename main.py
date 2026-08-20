from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from gradio_client import Client, handle_file
import tempfile
import os
import shutil

app = FastAPI()

# XTTS Gradio Space
XTTS_SPACE = "https://applore-xtts-voice-cloning-demo.hf.space"

# نفتح اتصال Gradio مرة واحدة
client = Client(XTTS_SPACE)


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
                opacity: .5;
                cursor: not-allowed;
            }

            audio {
                width: 100%;
                margin-top: 20px;
            }

            #download {
                display: none;
                width: 100%;
                box-sizing: border-box;
                margin-top: 12px;
                padding: 13px;
                background: #eee;
                color: #111;
                text-align: center;
                text-decoration: none;
                border-radius: 8px;
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
                اختاري ملف صوتي قصير، اكتبي النص، ثم اضغطي توليد الصوت.
            </p>

            <input
                id="file"
                type="file"
                accept="audio/*"
            >

            <textarea
                id="text"
                rows="5"
                placeholder="اكتبي النص الذي تريدين تحويله إلى صوت..."
            ></textarea>

            <button id="generateBtn" onclick="generate()">
                🎙️ توليد الصوت
            </button>

            <div id="status"></div>

            <audio id="audio" controls></audio>

            <a id="download" download="generated_voice.wav">
                ⬇️ تحميل الصوت
            </a>

        </div>

        <script>
        async function generate() {

            const fileInput = document.getElementById("file");
            const textInput = document.getElementById("text");
            const status = document.getElementById("status");
            const audio = document.getElementById("audio");
            const download = document.getElementById("download");
            const button = document.getElementById("generateBtn");

            const file = fileInput.files[0];
            const text = textInput.value.trim();

            if (!file) {
                status.innerText = "❌ اختاري ملف صوتي أولاً";
                return;
            }

            if (!text) {
                status.innerText = "❌ اكتبي النص أولاً";
                return;
            }

            button.disabled = true;
            status.innerText = "⏳ جاري توليد الصوت... قد يستغرق بعض الوقت";

            audio.removeAttribute("src");
            download.style.display = "none";

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

                if (blob.size === 0) {
                    throw new Error("تم إنشاء ملف صوتي فارغ");
                }

                const url = URL.createObjectURL(blob);

                audio.src = url;
                audio.load();

                download.href = url;
                download.style.display = "block";

                status.innerText =
                    "✅ تم توليد الصوت! اضغطي ▶️ للتشغيل";

            } catch (error) {

                console.error(error);

                status.innerText =
                    "❌ حدث خطأ: " + error.message;

            } finally {

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

    temp_path = None
    result_path = None

    try:

        # إنشاء ملف مؤقت للصوت المرفوع
        suffix = os.path.splitext(file.filename or ".wav")[1] or ".wav"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_path = temp_file.name

            shutil.copyfileobj(
                file.file,
                temp_file
            )

        # إرسال الطلب إلى Gradio بالطريقة الصحيحة
        result = client.predict(
            text,
            handle_file(temp_path),
            "ar",
            api_name="/predict"
        )

        # نتيجة Gradio تكون عادة مسار ملف الصوت الناتج
        if not result:
            raise Exception("XTTS لم يرجع ملف صوتي")

        if isinstance(result, (list, tuple)):
            result = result[0]

        # بعض إصدارات Gradio ترجع dict
        if isinstance(result, dict):

            if "path" in result:
                result_path = result["path"]

            elif "url" in result:
                raise Exception(
                    "XTTS أعاد رابطًا بدل ملف محلي"
                )

        else:
            result_path = str(result)

        if not result_path or not os.path.exists(result_path):
            raise Exception(
                f"لم يتم العثور على ملف الصوت الناتج: {result_path}"
            )

        # قراءة الصوت
        with open(result_path, "rb") as audio_file:
            audio_data = audio_file.read()

        if not audio_data:
            raise Exception("ملف الصوت الناتج فارغ")

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition":
                    'inline; filename="generated_voice.wav"'
            }
        )

    except Exception as e:

        print("XTTS ERROR:", repr(e))

        return Response(
            content=f'{{"detail":"{str(e)}"}}',
            status_code=500,
            media_type="application/json"
        )

    finally:

        # حذف الملف المؤقت الذي رفعه المستخدم
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": "Voice Clone AI",
        "xtts_space": XTTS_SPACE
    }
