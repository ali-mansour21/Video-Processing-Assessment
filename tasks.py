import shlex, subprocess
from pathlib import Path
from celery_app import celery_app

def _run(cmd:str):
    process = subprocess.run(shlex.split(cmd),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if process.returncode != 0 :
        raise RuntimeError(process.stdout)
    return process.stdout

def _atomic_replace(tmp:Path,final:Path):
    final.parent.mkdir(parents=True,exist_ok=True)
    tmp.replace(final)

@celery_app.task(acks_late=True)
def merge_task(paths:list[str],merged_out:str)->str:
    merged_out = Path(merged_out)
    job_dir = merged_out.parent
    tmp_dir = job_dir / "temp"
    tmp_dir.mkdir(parents=True,exist_ok=True)

    normalized = []
    for i,src in enumerate(paths,1):
        norm = tmp_dir / f"n{i:02d}.mp4"
        _run(f'ffmpeg -y -hide_banner -loglevel error -i "{src}" '
            f'-vf "scale=1280:-2:force_original_aspect_ratio=decrease,'
            f'pad=1280:720:(1280-iw)/2:(720-ih)/2,setsar=1" '
            f'-r 30 -c:v libx264 -preset veryfast -crf 23 '
            f'-c:a aac -ar 44100 -ac 2 "{norm}"'
            )
        normalized.append(norm)

    
    listfile = tmp_dir / "list.txt"
    listfile.write_text("".join([f"file '{p.as_posix()}'\n" for p in normalized]))
    merged_tmp = merged_out.with_suffix(".tmp.mp4")
    _run(f'ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "{listfile}" -c copy "{merged_tmp}"')
    _atomic_replace(merged_tmp, merged_out)
    return str(merged_out)

@celery_app.task(acks_late=True)
def watermark_task(merged_path: str, logo_path: str, final_out: str) -> str:
    merged_path = Path(merged_path)
    final_out = Path(final_out)
    tmp = final_out.with_suffix(".tmp.mp4")
    _run(
        f'ffmpeg -y -hide_banner -loglevel error -i "{merged_path}" -i "{logo_path}" '
        f'-filter_complex "[1:v]scale=200:-1,format=rgba,colorchannelmixer=aa=0.35[wm];'
        f'[0:v][wm]overlay=main_w-overlay_w-10:main_h-overlay_h-10:enable=\'between(t,0,3)\'" '
        f'-c:v libx264 -preset veryfast -crf 23 -c:a copy -movflags +faststart "{tmp}"'
        )
    _atomic_replace(tmp, final_out)
    return str(final_out)

def _probe_duration(path: Path) -> float:
    try:
        out = _run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"')
        return float(out.strip())
    except Exception:
        return 0.0

@celery_app.task(acks_late=True)
def thumbnail_task(final_video: str, thumb_out: str) -> str:
    final_video = Path(final_video)
    thumb_out = Path(thumb_out)
    tmp = thumb_out.with_suffix(".tmp.png")
    dur = _probe_duration(final_video)
    if dur >= 5:
        cmd = f'ffmpeg -y -hide_banner -loglevel error -ss 5 -i "{final_video}" -frames:v 1 -q:v 2 "{tmp}"'
    else:
        cmd = f'ffmpeg -y -hide_banner -loglevel error -sseof -1 -i "{final_video}" -frames:v 1 -q:v 2 "{tmp}"'
    _run(cmd)
    _atomic_replace(tmp, thumb_out)
    return str(thumb_out)