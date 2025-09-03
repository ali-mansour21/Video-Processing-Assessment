from pathlib import Path
from fastapi import FastAPI,UploadFile,File, HTTPException
import uuid
from settings import BASE_URL, VIDEOS_DIR
app = FastAPI(title="Video Processing Service")


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

    for i, f in enumerate(videos, start=1):
        safe_name = Path(f.filename or f"input{i}.mp4").name
        dst = uploads_dir / f"{i:02d}-{safe_name}"
        data = await f.read()
        dst.write_bytes(data)
    
    video_url = f"{BASE_URL}/videos/{job_id}/final.mp4"
    thumb_url = f"{BASE_URL}/videos/{job_id}/thumb.png"

    return {"video_url": video_url, "thumbnail_url": thumb_url}