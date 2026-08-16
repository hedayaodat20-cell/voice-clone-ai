from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid

app = FastAPI()

# السماح لموقع GitHub Pages بالاتصال بالـ Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hedayaodat20-cell.github.io"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Voice Clone AI backend is running"
    }


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):

    extension = os.path.splitext(file.filename)[1]

    filename = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    with open(file_path, "wb") as audio_file:
        audio_file.write(await file.read())

    return {
        "message": "تم رفع الملف بنجاح",
        "filename": filename
    }
