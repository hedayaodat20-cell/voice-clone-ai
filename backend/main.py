from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "index.html")
    )


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
