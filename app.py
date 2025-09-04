from pathlib import Path
from celery import chain
from fastapi import FastAPI,UploadFile,File, HTTPException
from fastapi.staticfiles import StaticFiles
from tasks import merge_task, watermark_task, thumbnail_task
import uuid
from settings import BASE_URL, VIDEOS_DIR
app = FastAPI(title="Video Processing Service")

app.mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")
LOGO_PATH = Path("logo.png").resolve()
@app.get("/")
def read_root():
    return {"message":"Hello World"}

@app.post("/videos/merge")
async def merge_vidoes(videos: list[UploadFile] = File(...)):
    if not (2<= len(videos) <= 5):
        raise HTTPException(status_code=400, detail="You Should Provide Between 2 and 5 Video Files.")
    
    job_id = uuid.uuid4().hex[:8]
    job_dir = VIDEOS_DIR / job_id
    uploads_dir = job_dir / "uploads"
    uploads_dir.mkdir(parents=True,exist_ok=True)

    input_paths: list[str] = [] 
    for i, f in enumerate(videos, start=1):
        safe_name = Path(f.filename or f"input{i}.mp4").name
        dst = uploads_dir / f"{i:02d}-{safe_name}"
        data = await f.read()
        dst.write_bytes(data)
        input_paths.append(str(dst))
    
    merged_path = str(job_dir / "merged.mp4")
    final_path  = str(job_dir / "final.mp4")
    thumb_path  = str(job_dir / "thumb.png")

    chain(
        merge_task.s(input_paths, merged_path),
        watermark_task.s(str(LOGO_PATH), final_path),
        thumbnail_task.s(thumb_path),
    ).apply_async()

    video_url = f"{BASE_URL}/videos/{job_id}/final.mp4"
    thumb_url = f"{BASE_URL}/videos/{job_id}/thumb.png"

    return {"video_url": video_url, "thumbnail_url": thumb_url}