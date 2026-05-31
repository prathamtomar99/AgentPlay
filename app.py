from flask import Flask, jsonify, send_file
from concurrent.futures import ThreadPoolExecutor
import uuid
import os
import logging

from Utils.User import VideoOBJ
from config import MAX_WORKERS
from Utils.Translation import TranslatorAgent
from Utils.Audio import Audio
from Utils.Rag import Rag

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

ACTIVE_LOCKS = {}               # Tracks tasks using id i.e. ACTIVE_LOCKS[LOCK_KEY] = THREAD_ID
TASK_REGISTRY = {}              # Tracks thread status using execution_id
VIDEO_CACHE = {}                # Safely stores the finished VideoOBJ
SEGMENT_VIDEOID_LANG_CACHE = {} # Tracks completed audio segments f"{VIDEO_ID}_{TARGET_LANGUAGE}_{SEGMENT_NO}"

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _is_task_running(lock_key):
    """Returns True if a task for lock_key is currently processing."""
    if lock_key in ACTIVE_LOCKS:
        execution_id = ACTIVE_LOCKS[lock_key]
        return TASK_REGISTRY.get(execution_id, {}).get("status") == "processing"
    return False


def _submit_task(lock_key, task_func, *args, **kwargs):
    """Registers and submits a background task. Returns the new execution_id."""
    execution_id = str(uuid.uuid4())
    ACTIVE_LOCKS[lock_key] = execution_id
    TASK_REGISTRY[execution_id] = {"status": "processing", "result": None}
    logger.debug("Submitting background task %s (execution_id=%s)", lock_key, execution_id)
    executor.submit(universal_background_runner, execution_id, lock_key, task_func, *args, **kwargs)
    return execution_id


# ─────────────────────────────────────────────
# BACKGROUND RUNNER
# ─────────────────────────────────────────────

def universal_background_runner(execution_id, lock_key, task_func, *args, **kwargs):
    logger.info(f"Starting Background Task for {lock_key}.")
    try:
        result = task_func(*args, **kwargs)
        TASK_REGISTRY[execution_id] = {"status": "complete", "result": result}

        if isinstance(result, VideoOBJ):
            video_id = args[0]  # First arg is always video_id
            VIDEO_CACHE[video_id] = result
            logger.info(f"VideoOBJ cached for video_id: {video_id}")

        if isinstance(result, str) and result.startswith("Completed"):
            SEGMENT_VIDEOID_LANG_CACHE[lock_key] = TASK_REGISTRY[execution_id]["result"]
            logger.info(f"Segment cached for lock_key: {lock_key}")

    except Exception as e:
        TASK_REGISTRY[execution_id] = {"status": "failed", "result": str(e)}
        logger.exception(f"Task Failed for {lock_key}: {e}")


# ─────────────────────────────────────────────
# CORE TASKS
# ─────────────────────────────────────────────

def run_translate_audio(VIDEO_ID, TARGET_LANGUAGE_ABBREVIATION, SEGMENT_NO, PREVIOUS_SEGMENT, CURRENT_SEGMENT, FUTURE_SEGMENT):
    FILE_NAME = f"{TARGET_LANGUAGE_ABBREVIATION}{SEGMENT_NO}.mp3"
    try:
        TRANSLATED_TEXT = TranslatorAgent().call(
            PREVIOUS_SEGMENT=PREVIOUS_SEGMENT,
            CURRENT_SEGMENT=CURRENT_SEGMENT,
            FUTURE_SEGMENT=FUTURE_SEGMENT,
            TARGET_LANGUAGE_ABBREVIATION=TARGET_LANGUAGE_ABBREVIATION,
        )

        output_path = os.path.join("Data", VIDEO_ID, FILE_NAME)
        os.makedirs(os.path.join("Data", VIDEO_ID), exist_ok=True)

        Audio().tts(
            TEXT=TRANSLATED_TEXT,
            LANG_ABBREVIATION=TARGET_LANGUAGE_ABBREVIATION,
            OUTPUT_FILE=output_path,
        )

    except Exception as e:
        logger.error(f"Error in {FILE_NAME}: {e}")
        return f"Error in {FILE_NAME} : {e}"

    logger.info(f"Completed for: {FILE_NAME}")
    return f"Completed : {FILE_NAME}"


def run_generate_embeddings(transcript_data: dict):
    """Wraps Rag.process_and_store_transcript for background execution."""
    rag = Rag()
    rag.initialize_collection()
    result = rag.process_and_store_transcript(data_segment=transcript_data)
    return result  # Returns "Transcript Generated for : {VIDEO_ID}." on success


def _submit_segment_tasks(obj, VIDEO_ID, TARGET_LANGUAGE, start_index):
    segments = obj.transcript_english["segments"]
    submitted = []
    for i in range(max(0, start_index - 1), min(start_index + 10, len(segments))):
        LOCK_KEY = f"{VIDEO_ID}_{TARGET_LANGUAGE}_{i}"
        if _is_task_running(LOCK_KEY) or LOCK_KEY in SEGMENT_VIDEOID_LANG_CACHE:
            continue

        PREVIOUS_SEGMENT = segments[i - 1]["text"] if i - 1 >= 0 else None
        CURRENT_SEGMENT = segments[i]["text"]
        FUTURE_SEGMENT = segments[i + 1]["text"] if i + 1 < len(segments) else None

        _submit_task(LOCK_KEY, run_translate_audio, VIDEO_ID, TARGET_LANGUAGE, i, PREVIOUS_SEGMENT, CURRENT_SEGMENT, FUTURE_SEGMENT)
        submitted.append(i)
    return submitted


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def health():
    return "Working"


@app.route('/lock_status/<LOCK_KEY>')
def lock_status(LOCK_KEY):
    if LOCK_KEY not in ACTIVE_LOCKS:
        return jsonify({"status": "Not Found", "message": f"No active task found for {LOCK_KEY}."}), 404

    execution_id = ACTIVE_LOCKS[LOCK_KEY]
    current_status = TASK_REGISTRY.get(execution_id, {}).get("status", "unknown")

    if current_status == "processing":
        return jsonify({"status": "Processing", "message": f"{LOCK_KEY} is in progress."}), 202

    elif current_status == "complete":
        ACTIVE_LOCKS.pop(LOCK_KEY, None)
        TASK_REGISTRY.pop(execution_id, None)
        return jsonify({"status": "Completed", "message": f"{LOCK_KEY} is Completed"}), 200

    elif current_status == "failed":
        error_detail = TASK_REGISTRY.get(execution_id, {}).get("result", "Unknown error")
        return jsonify({"status": "Failed", "message": f"{LOCK_KEY} failed.", "detail": error_detail}), 500

    return jsonify({"status": "Unknown", "message": "Unexpected task state."}), 500


@app.route('/initialise_object/<video_id>')
def initialise_object(video_id):
    LOCK_KEY = f"{video_id}_OBJ"

    if video_id in VIDEO_CACHE:
        return jsonify({"status": "complete", "message": "Already generated and ready!"}), 200

    if _is_task_running(LOCK_KEY):
        return jsonify({"status": "Processing", "message": "Video Initialization is currently in progress."}), 202

    if LOCK_KEY in ACTIVE_LOCKS:
        old_id = ACTIVE_LOCKS.pop(LOCK_KEY, None)
        if old_id:
            TASK_REGISTRY.pop(old_id, None)

    _submit_task(LOCK_KEY, VideoOBJ.create, video_id)
    return jsonify({"status": "processing", "message": "Initialization started."}), 202


@app.route('/show_transcript/<video_id>')
def show_transcript(video_id):
    try:
        if video_id in VIDEO_CACHE:
            obj = VIDEO_CACHE[video_id]
            if obj.is_transcript_exists:
                return jsonify({"transcript": obj.transcript_english}), 200
        return initialise_object(video_id)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/translate_audio/<VIDEO_ID>/<TARGET_LANGUAGE>/<int:SEGMENT_NO>')
def translate_audio_route(VIDEO_ID, TARGET_LANGUAGE, SEGMENT_NO):
    try:
        if VIDEO_ID not in VIDEO_CACHE:
            initialise_object(VIDEO_ID)
            return jsonify({"status": "processing", "message": "Video not ready. Initialization started. Retry shortly."}), 202

        obj = VIDEO_CACHE[VIDEO_ID]
        if not obj.is_transcript_exists:
            return jsonify({"error": "No transcript available for this video."}), 404

        submitted = _submit_segment_tasks(obj, VIDEO_ID, TARGET_LANGUAGE, SEGMENT_NO)
        return jsonify({
            "status": "Processing Segments",
            "message": f"Segment generation started for indices: {submitted}"
        }), 202

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/get_audio/<VIDEO_ID>/<TARGET_LANGUAGE>/<int:SEGMENT_NO>')
def get_audio(VIDEO_ID, TARGET_LANGUAGE, SEGMENT_NO):
    LOCK_KEY = f"{VIDEO_ID}_{TARGET_LANGUAGE}_{SEGMENT_NO}"
    FILE_NAME = f"{TARGET_LANGUAGE}{SEGMENT_NO}.mp3"
    FILE_PATH = os.path.join("Data", VIDEO_ID, FILE_NAME)

    if LOCK_KEY in SEGMENT_VIDEOID_LANG_CACHE and os.path.exists(FILE_PATH):
        return send_file(FILE_PATH, mimetype="audio/mpeg")

    if _is_task_running(LOCK_KEY):
        return jsonify({"status": "Processing", "message": f"Segment {SEGMENT_NO} is still being generated."}), 202

    if LOCK_KEY in ACTIVE_LOCKS:
        execution_id = ACTIVE_LOCKS[LOCK_KEY]
        task_status = TASK_REGISTRY.get(execution_id, {}).get("status")

        if task_status == "failed":
            error_detail = TASK_REGISTRY.get(execution_id, {}).get("result", "Unknown")
            ACTIVE_LOCKS.pop(LOCK_KEY, None)
            TASK_REGISTRY.pop(execution_id, None)
            return jsonify({"status": "Failed", "message": f"Segment {SEGMENT_NO} generation failed.", "detail": error_detail}), 500

        if task_status == "complete" and os.path.exists(FILE_PATH):
            SEGMENT_VIDEOID_LANG_CACHE[LOCK_KEY] = FILE_PATH
            ACTIVE_LOCKS.pop(LOCK_KEY, None)
            TASK_REGISTRY.pop(execution_id, None)
            return send_file(FILE_PATH, mimetype="audio/mpeg")

    if VIDEO_ID not in VIDEO_CACHE:
        initialise_object(VIDEO_ID)
        return jsonify({"status": "processing", "message": "Video not ready. Initialization started. Retry shortly."}), 202

    obj = VIDEO_CACHE[VIDEO_ID]
    if not obj.is_transcript_exists:
        return jsonify({"error": "No transcript available for this video."}), 404

    segments = obj.transcript_english
    if SEGMENT_NO >= len(segments):
        return jsonify({"error": f"Segment {SEGMENT_NO} out of range."}), 400

    PREVIOUS_SEGMENT = segments[SEGMENT_NO - 1]["text"] if SEGMENT_NO - 1 >= 0 else None
    CURRENT_SEGMENT = segments[SEGMENT_NO]["text"]
    FUTURE_SEGMENT = segments[SEGMENT_NO + 1]["text"] if SEGMENT_NO + 1 < len(segments) else None

    _submit_task(LOCK_KEY, run_translate_audio, VIDEO_ID, TARGET_LANGUAGE, SEGMENT_NO, PREVIOUS_SEGMENT, CURRENT_SEGMENT, FUTURE_SEGMENT)
    return jsonify({"status": "Processing", "message": f"Segment {SEGMENT_NO} generation triggered. Retry shortly."}), 202


@app.route('/generate_embeddings/<VIDEO_ID>')
def generate_embeddings(VIDEO_ID):
    """Generates and stores hybrid embeddings for a video's transcript in Qdrant."""
    logger.info("generate_embeddings requested for %s", VIDEO_ID)
    try:
        if VIDEO_ID not in VIDEO_CACHE:
            initialise_object(VIDEO_ID)
            return jsonify({"status": "processing", "message": "Video not ready. Initialization started. Retry shortly."}), 202

        obj = VIDEO_CACHE[VIDEO_ID]
        if not obj.is_transcript_exists:
            return jsonify({"error": "No transcript available for this video."}), 404

        LOCK_KEY = f"{VIDEO_ID}_RAG"

        if Rag().video_exists(VIDEO_ID):
            logger.info("generate_embeddings: embeddings already exist for %s", VIDEO_ID)
            return jsonify({"status": "complete", "message": "Embeddings already exist for this video."}), 200

        if _is_task_running(LOCK_KEY):
            return jsonify({"status": "Processing", "message": "Embedding generation is already in progress."}), 202

        if LOCK_KEY in ACTIVE_LOCKS:
            old_id = ACTIVE_LOCKS.pop(LOCK_KEY, None)
            if old_id:
                TASK_REGISTRY.pop(old_id, None)

        _submit_task(LOCK_KEY, run_generate_embeddings, obj.transcript_original)
        logger.info("generate_embeddings: submitted for %s", VIDEO_ID)
        return jsonify({
            "status": "Processing Embedding",
            "message": f"Embedding generation started for: {VIDEO_ID}"
        }), 202

    except Exception as e:
        logger.exception("generate_embeddings failed for %s", VIDEO_ID)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/query_rag/<VIDEO_ID>/<QUERY>')
@app.route('/query_rag/<VIDEO_ID>/<QUERY>/<int:LIMIT>')
def query_rag(VIDEO_ID, QUERY, LIMIT=5):
    logger.info("query_rag requested for VIDEO_ID=%s QUERY=%s LIMIT=%s", VIDEO_ID, QUERY, LIMIT)
    try:
        if VIDEO_ID not in VIDEO_CACHE:
            initialise_object(VIDEO_ID)
            return jsonify({"status": "processing", "message": "Video not ready. Initialization started. Retry shortly."}), 202

        obj = VIDEO_CACHE[VIDEO_ID]
        if not obj.is_transcript_exists:
            return jsonify({"error": "No transcript available for this video."}), 404

        rag = Rag()
        if not rag.video_exists(VIDEO_ID):
            LOCK_KEY = f"{VIDEO_ID}_RAG"
            if not _is_task_running(LOCK_KEY):
                _submit_task(LOCK_KEY, run_generate_embeddings, obj.transcript_original)
            return jsonify({
                "status": "processing",
                "message": "Embeddings not ready yet. Generation triggered. Retry shortly."
            }), 202

        results = rag.hybrid_search(video_id=VIDEO_ID, user_query=QUERY, limit=LIMIT)

        formatted = [
            {
                "text": point.payload.get("text"),
                "start_time": point.payload.get("start_time"),
                "duration": point.payload.get("duration"),
                "score": point.score,
            }
            for point in results
        ]

        logger.info("query_rag: returning %d results for %s", len(formatted), VIDEO_ID)
        return jsonify({"video_id": VIDEO_ID, "query": QUERY, "results": formatted}), 200

    except Exception as e:
        logger.exception("query_rag failed for %s", VIDEO_ID)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)