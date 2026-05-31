# Singleton Class for TranscriptStore
# Return None is transcript is not available

from Utils.Singleton import Singleton
from youtube_transcript_api import YouTubeTranscriptApi
from Utils.Exception import UnsupportedLanguage
from config import SUPPORTED_LANGUAGES
import logging
import json
import pprint

logget = logging.getLogger(__name__)

@Singleton
class TranscriptStore:
    def __init__(self):
        self.ytt_api = YouTubeTranscriptApi()
    
    def list_available_languages(self,video_id):
        langs = []
        list = self.ytt_api.list(video_id)
        for transcript in list:
            langs.append(transcript.language)
        return langs
    
    def get_transcript(self,video_id):
        for idx,lang in enumerate(SUPPORTED_LANGUAGES):
            try:
                return self.ytt_api.fetch(video_id,languages=[lang]) , SUPPORTED_LANGUAGES[idx]
            except Exception as e:
                logget.debug(f"[YT_Transcript] : Unsupported languages not avaibale in {SUPPORTED_LANGUAGES[idx]}.")
                continue
    
        return None, None # we can also raise error
        # raise UnsupportedLanguage("Langugages not supported")

    def get_segments(self,video_id):
        transcript,lang = self.get_transcript(video_id)
        if(transcript is None):
            return None
        segments = []
        for segment in transcript[:20]:
            # print(segment)
            seg = {}
            seg["text"] = segment.text
            seg["start"] = segment.start
            seg["duration"] = segment.duration
            segments.append(seg)

        data = {
            "language" : lang,
            "video_id" : video_id,
            "segments" : segments
        }

        data_fixed = self.fix_overlapping_segments(data)
        return json.dumps(data_fixed,indent = 4)
    
    def fix_overlapping_segments(self,data_segment: dict) -> dict:
        segments = data_segment.get("segments", [])
        
        for i in range(len(segments) - 1):
            current_seg = segments[i]
            next_seg = segments[i + 1]
            
            current_end = current_seg["start"] + current_seg["duration"]
            
            # Check for overlap
            if current_end > next_seg["start"]:
                new_duration = next_seg["start"] - current_seg["start"]
                current_seg["duration"] = max(0.01, round(new_duration, 3))
                
        data_segment["segments"] = segments
        return data_segment
    

if __name__ == "__main__":
    yt_api = TranscriptStore()
    logget.info(yt_api.list_available_languages("4O1Fk6edPkI"))
    
    data = json.loads(yt_api.get_segments("4O1Fk6edPkI"))
    logget.info(data["language"])
    logget.info(data["video_id"])
    for seg in (data["segments"])[:100]:
        logget.debug("\t %s", seg['text'])
        logget.debug("\t %s", seg['start'])
        logget.debug('\t %s', seg['duration'])
        logget.debug('')