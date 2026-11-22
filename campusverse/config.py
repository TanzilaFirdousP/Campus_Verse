import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = Path(os.getenv("CAMPUSVERSE_DB", DATA_DIR / "campusverse.db"))
BACKEND = os.getenv("CAMPUSVERSE_BACKEND", "ollama").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
RECENT_MESSAGES = 10
RELEVANT_MEMORIES = 8
