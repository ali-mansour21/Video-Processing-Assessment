import shlex, subprocess
import time,json
from pathlib import Path
from celery_app import celery_app
from celery.exceptions import SoftTimeLimitExceeded

def _run(cmd:str):
    process = subprocess.run(shlex.split(cmd),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if process.returncode != 0 :
        raise RuntimeError(process.stdout)
    return process.stdout

def _atomic_replace(tmp:Path,final:Path):
    final.parent.mkdir(parents=True,exist_ok=True)
    tmp.replace(final)

@celery_app.task(
        acks_late=True, 
        autoretry_for=(RuntimeError, SoftTimeLimitExceeded),
        retry_kwargs={"max_retries": 2},
        retry_backoff=True,         
        retry_backoff_max=300,
        retry_jitter=True, 
)
def merge_task(paths:list[str],merged_out:str)->str:
    merged_out_path = Path(merged_out)
    job_dir = merged_out_path.parent
    tmp_dir = job_dir / "temp"
    tmp_dir.mkdir(parents=True,exist_ok=True)

    try:
        normalized = []
        for i, src in enumerate(paths, 1):
            norm = tmp_dir / f"n{i:02d}.mp4"
            out = _run(
                f'ffmpeg -y -hide_banner -loglevel error -i "{src}" '
                f'-vf "scale=1280:-2:force_original_aspect_ratio=decrease,'
                f'pad=1280:720:(1280-iw)/2:(720-ih)/2,setsar=1" '
                f'-r 30 -c:v libx264 -preset veryfast -crf 23 '
                f'-c:a aac -ar 44100 -ac 2 "{norm}"'
            )
            _write_log(job_dir, f"merge_norm_{i:02d}", out)
            normalized.append(norm)

        listfile = tmp_dir / "list.txt"
        listfile.write_text("".join([f"file '{p.as_posix()}'\n" for p in normalized]))

        merged_tmp = merged_out_path.with_suffix(".tmp.mp4")
        out = _run(
            f'ffmpeg -y -hide_banner -loglevel error '
            f'-f concat -safe 0 -i "{listfile}" -c copy "{merged_tmp}"'
        )
        _write_log(job_dir, "merge_concat", out)
        _atomic_replace(merged_tmp, merged_out_path)
        return str(merged_out_path)

    except Exception as e:
        _write_error(job_dir, "merge", str(e), {"outputs": str(merged_out_path)})
        raise

@celery_app.task(
        acks_late=True, 
        autoretry_for=(RuntimeError, SoftTimeLimitExceeded),
        retry_kwargs={"max_retries": 2},
        retry_backoff=True,         
        retry_backoff_max=300,
        retry_jitter=True,
)
def watermark_task(merged_path: str, logo_path: str, final_out: str) -> str:
    merged_path = Path(merged_path)
    final_out = Path(final_out)
    job_dir = final_out.parent
    tmp = final_out.with_suffix(".tmp.mp4")
    cmd = (
        f'ffmpeg -y -hide_banner -loglevel error '
        f'-i "{merged_path}" -i "{logo_path}" '
        f'-filter_complex "[1:v]scale=200:-1,format=rgba,'
        f'colorchannelmixer=aa=0.35[wm];'
        f'[0:v][wm]overlay=main_w-overlay_w-10:main_h-overlay_h-10:'
        f'enable=\'between(t,0,3)\'" '
        f'-c:v libx264 -preset veryfast -crf 23 -c:a copy -movflags +faststart "{tmp}"'
    )
    try:
        out = _run(cmd)
        _write_log(job_dir, "watermark", out)
        _atomic_replace(tmp, final_out)
        return str(final_out)
    except Exception as e:
        _write_error(job_dir, "watermark", str(e), {"cmd": cmd})
        raise

def _probe_duration(path: Path) -> float:
    try:
        out = _run(
            f'ffprobe -v error -show_entries format=duration '
            f'-of default=noprint_wrappers=1:nokey=1 "{path}"'
        ).strip()
        return float(out)
    except Exception:
        return 0.0

@celery_app.task(
        acks_late=True, 
        autoretry_for=(RuntimeError, SoftTimeLimitExceeded),
        retry_kwargs={"max_retries": 2},
        retry_backoff=True,         
        retry_backoff_max=300,
        retry_jitter=True
)
def thumbnail_task( final_video: str, thumb_out: str) -> str:
    final_video = Path(final_video)
    thumb_out = Path(thumb_out)
    job_dir = thumb_out.parent
    tmp = thumb_out.with_suffix(".tmp.png")
    dur = _probe_duration(final_video)
    try:
        dur = _probe_duration(final_video)
        if dur >= 5:
            cmd = f'ffmpeg -y -hide_banner -loglevel error -ss 5 -i "{final_video}" -frames:v 1 -q:v 2 "{tmp}"'
        else:
            cmd = f'ffmpeg -y -hide_banner -loglevel error -sseof -1 -i "{final_video}" -frames:v 1 -q:v 2 "{tmp}"'
        out = _run(cmd)
        _write_log(job_dir, "thumbnail", out)
        _atomic_replace(tmp, thumb_out)
        return str(thumb_out)
    except Exception as e:
        _write_error(job_dir, "thumbnail", str(e), {"final_video": str(final_video)})
        raise


def _write_log(job_dir: Path, step: str, text: str):
    logs = job_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / f"{step}.log").write_text(text)

def _write_error(job_dir: Path, step: str, message: str, details: dict | None = None):
    error = {
        "step": step,
        "message": message,
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "details": details or {},
    }
    (job_dir / "error.json").write_text(json.dumps(error, indent=2))