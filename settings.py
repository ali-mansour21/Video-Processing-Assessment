import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_URL   = os.getenv("BASE_URL", "http://localhost:5000")
VIDEOS_DIR = Path(os.getenv("VIDEOS_DIR", "videos")).resolve()
REDIS_URL  = os.getenv("REDIS_URL", "redis://localhost:6379/0")

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)