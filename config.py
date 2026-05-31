# configurations of project
MAX_WORKERS = 30 # max number of requests to be executed in parallel (app.py)
OUTPUT_FOLDER = "Data"

from polyrouter import LLMOrchestrator
import os
from dotenv import load_dotenv
import logging
import sys

load_dotenv()

# Centralized logging: single root logger writing to a file
LOG_FILE = "poly_router.log"

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Remove any pre-existing handlers to avoid duplicates
for h in list(root_logger.handlers):
    root_logger.removeHandler(h)

file_handler = logging.FileHandler(LOG_FILE, mode="w")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# Optional: also keep a minimal console output (comment out if not desired)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Only your library logs at DEBUG
logging.getLogger("polyrouter").setLevel(logging.DEBUG)

# Silence noisy third-party loggers
for noisy in ("httpx", "httpcore", "hpack", "cerebras", "urllib3", "groq", "google_genai"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

# Ensure werkzeug (Flask dev server) logs propagate to root file handler
werkzeug_logger = logging.getLogger("werkzeug")
for h in list(werkzeug_logger.handlers):
    werkzeug_logger.removeHandler(h)
werkzeug_logger.propagate = True


GROQ_MODEL = [
    # "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct", 
    "qwen/qwen3-32b"
]
GROQ_KEYS = [
    os.getenv("GROQ_API_KEY0"),
    os.getenv("GROQ_API_KEY1"),
    os.getenv("GROQ_API_KEY2"),
    os.getenv("GROQ_API_KEY3"),
    os.getenv("GROQ_API_KEY4"),
    os.getenv("GROQ_API_KEY5"),
]

GEMINI_MODEL = [
    # "gemini-2.5-flash-lite"
    "gemini-2.5-flash",
]
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY0"),
    os.getenv("GEMINI_API_KEY1"),
    os.getenv("GEMINI_API_KEY2"),
    os.getenv("GEMINI_API_KEY3"),
    os.getenv("GEMINI_API_KEY4"),
    os.getenv("GEMINI_API_KEY5"),
    os.getenv("GEMINI_API_KEY6"),
    os.getenv("GEMINI_API_KEY7")
]

CEREBRAS_MODEL = [
    "gpt-oss-120b",
    "zai-glm-4.7"
]
CEREBRAS_KEYS = [
    os.getenv("CEREBRAS_API_KEY0"),
    os.getenv("CEREBRAS_API_KEY1"),
    os.getenv("CEREBRAS_API_KEY2"),
    os.getenv("CEREBRAS_API_KEY3"),
    os.getenv("CEREBRAS_API_KEY4"),
    os.getenv("CEREBRAS_API_KEY5")
]

# Voice configurations
VOICE_CONFIGS = {
    'en': "en-US-JennyNeural",
    'hi': "hi-IN-SwaraNeural",
    'es': "es-MX-JorgeNeural",
    'fr': "fr-FR-HenriNeural",
    'de': "de-DE-KillianNeural",
    'ja': "ja-JP-KeitaNeural",
    'ko': "ko-KR-SunHiNeural",
    'zh': "zh-CN-XiaoxiaoNeural",
    'it': "it-IT-DiegoNeural",
    'pt': "pt-BR-AntonioNeural",
    'ru': "ru-RU-DmitryNeural",
    'nl': "nl-NL-MaartenNeural",
    'tr': "tr-TR-AhmetNeural",
    'pl': "pl-PL-MarekNeural",
    'id': "id-ID-ArdiNeural",
    'th': "th-TH-NiwatNeural",
    'vi': "vi-VN-HoaiMyNeural"
}

LANGUAGE_MAP = {
    'en': "English",
    'hi': "Hindi",
    'es': "Spanish",
    'fr': "French",
    'de': "German",
    'ja': "Japanese",
    'ko': "Korean",
    'zh': "Chinese (Mandarin)",
    'it': "Italian",
    'pt': "Portuguese (Brazilian)",
    'ru': "Russian",
    'nl': "Dutch",
    'tr': "Turkish",
    'pl': "Polish",
    'id': "Indonesian",
    'th': "Thai",
    'vi': "Vietnamese"
}


SUPPORTED_LANGUAGES = ['en','hi','nl'] # languages which we can fetch YT transcript api, can be increased depending upon the multilingual trasnlations model support
