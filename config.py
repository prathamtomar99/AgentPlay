# configurations of project
MAX_WORKERS = 30 # max number of requests to be executed in parallel (translate -> tts pipeline)
OUTPUT_FOLDER = "Data"

from polyrouter import LLMOrchestrator
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# logging.basicConfig(
#     filename="poly_router.log",
#     level = logging.DEBUG,
#     format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     filemode="w",
# )

# # Only your library logs
# logging.getLogger("polyrouter").setLevel(logging.DEBUG)

# # Silence noisy third-party loggers
# logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("httpcore").setLevel(logging.WARNING)
# logging.getLogger("hpack").setLevel(logging.WARNING)
# logging.getLogger("cerebras").setLevel(logging.WARNING)
# logging.getLogger("urllib3").setLevel(logging.WARNING)
# logging.getLogger("groq").setLevel(logging.WARNING)
# logging.getLogger("google_genai").setLevel(logging.WARNING)


GROQ_MODEL = [
    "llama-3.1-8b-instant",
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
    "gemini-2.5-flash-lite"
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
    # "llama3.1-8b", 
]
CEREBRAS_KEYS = [
    os.getenv("CEREBRAS_API_KEY0"),
    os.getenv("CEREBRAS_API_KEY1"),
    os.getenv("CEREBRAS_API_KEY2"),
    os.getenv("CEREBRAS_API_KEY3"),
    os.getenv("CEREBRAS_API_KEY4"),
    os.getenv("CEREBRAS_API_KEY5")
]