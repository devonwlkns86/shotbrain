import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .ocr import extract_text

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "app" / "uploads"
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ShotBrain")

# Serve uploads so we can preview images
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Simple in-memory store for MVP
STORE = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    items = list(reversed(STORE[-10:]))  # show last 10
    for it in items:
        it["image_url"] = f"/uploads/{it['filename']}"
    return templates.TemplateResponse("index.html", {"request": request, "items": items})

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"]:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    safe_name = file.filename.replace(" ", "_")
    dest_path = UPLOAD_DIR / safe_name

    # Avoid overwriting existing files
    counter = 1
    while dest_path.exists():
        stem = Path(safe_name).stem
        ext = Path(safe_name).suffix
        dest_path = UPLOAD_DIR / f"{stem}_{counter}{ext}"
        counter += 1

    # Save file to disk
    with open(dest_path, "wb") as out:
        out.write(await file.read())

    # OCR extract
    text = extract_text(str(dest_path))

    # Save to in-memory list
    STORE.append({
        "filename": dest_path.name,
        "text": text,
    })

    # Back to home to show results
    return RedirectResponse(url="/", status_code=303)
