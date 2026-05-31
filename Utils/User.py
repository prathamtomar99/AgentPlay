import json
import logging
from concurrent.futures import ThreadPoolExecutor

from Utils.Rag import Rag
from Utils.YT_Transcript import TranscriptStore
from Utils.Translation import TranslatorAgent

class VideoOBJ:
    def __init__(self, video_id, transcript_original, transcript_english, source_lang):
        self.video_id = video_id

        if transcript_original is None:
            self.is_transcript_exists = False
        else:
            self.original_video_lang = source_lang
            self.is_transcript_exists = True
            self.audio_generated_languages = []
            self.is_summary_generated = False
            self.summary = ""
            self.transcript_original = transcript_original
            self.transcript_english = transcript_english
            self.embeddings_generated = False
        logging.getLogger(__name__).info(f"Created {video_id}_OBJ")

    @staticmethod
    def _translate_single_segment(idx, segment_text, prev_segment, next_segment, start, duration):
        """Helper method to run in a background thread."""
        try:
            translated_text = TranslatorAgent().call(
                prev_segment,
                segment_text,
                next_segment,
                'en'
            )
            return idx, translated_text, start, duration
        except Exception as e:
            logging.getLogger(__name__).error(f"Translation failed for segment {idx}: {e}")
            # Fallback to the original text if the API fails, so the whole process doesn't crash
            return idx, segment_text , start, duration

    @classmethod
    def create(cls, video_id):
        logging.getLogger(__name__).debug(f"Inside Create Method: {video_id}")

        data = json.loads(TranscriptStore().get_segments(video_id))
        transcript_original = data.get("segments", [])
        source_lang = data.get("language", "")

        transcript_english = {
            "language": source_lang,
            "video_id": video_id,
            "segments": transcript_original
        }

        if source_lang != 'en':
            logging.getLogger(__name__).info("Translating to English concurrently.")
            transcript_english["language"] = 'en'
            
            tasks = []
            for idx, segment in enumerate(transcript_original):
                prev_segment = transcript_original[idx-1]["text"] if idx > 0 else None
                next_segment = transcript_original[idx+1]["text"] if idx < len(transcript_original)-1 else None
                
                tasks.append((idx, segment["text"], prev_segment, next_segment, segment["start"], segment["duration"]))

            results = []
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(cls._translate_single_segment, *task) 
                    for task in tasks
                ]
                
                for future in futures:
                    results.append(future.result())

            results.sort(key=lambda x: x[0])
            translated_segments = []
            for idx, translated_text, start, duration in results:
                translated_segments.append({
                    "text": translated_text,
                    "start": start,
                    "duration": duration
                })

            transcript_english["segments"] = translated_segments

        logging.getLogger(__name__).info("Creating VideoID OBJ")
        return cls(video_id, transcript_original, transcript_english, source_lang)