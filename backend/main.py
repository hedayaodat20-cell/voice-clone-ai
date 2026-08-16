from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Voice Clone AI backend is running"
    }


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    with open(file_path, "wb") as audio_file:
        audio_file.write(await file.read())

    return {
        "message": "تم رفع الملف بنجاح",
        "filename": file.filename
    }
