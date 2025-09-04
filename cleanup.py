import os
import time
from pathlib import Path
from settings import VIDEOS_DIR

MAX_AGE = 24 * 3600

def cleanup_videos():
    now = time.time()
    removed = []
    for job_dir in VIDEOS_DIR.iterdir():
        if job_dir.is_dir():
            age = now - job_dir.stat().st_mtime
            if age > MAX_AGE:
                for root, dirs, files in os.walk(job_dir,topdown=False):
                    for f in files:
                        try:
                            os.remove(Path(root) / f)
                        except Exception as e:
                            print(f"Failed to remove {f}: {e}")
                    for d in dirs:
                        try:
                            os.rmdir(Path(root) / d)
                        except Exception as e:
                            print(f"Failed to remove {d}: {e}")
                try:
                    os.rmdir(job_dir)
                    removed.append(job_dir.name)
                except Exception as e:
                    print(f"Failed to remove {job_dir}: {e}")
            
            if removed:
                print(f"Removed old jobs: {', '.join(removed)}")
            else:
                print("No old jobs found.")

if __name__ == "__main__":
    cleanup_videos()