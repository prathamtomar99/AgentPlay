# Singleton Class for TranscriptStore
# Return None is transcript is not available

from Utils.Singleton import Singleton
from youtube_transcript_api import YouTubeTranscriptApi
from Utils.Exception import UnsupportedLanguage
from config import SUPPORTED_LANGUAGES
import logging
import json

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
        for segment in transcript:
            # print(segment)
            seg = {}
            seg["text"] = segment.text
            seg["start"] = segment.start
            seg["duration"] = segment.duration
            segments.append(seg)

        data_json = {
            "language" : lang,
            "video_id" : video_id,
            "segments" : segments
        }
        return json.dumps(data_json,indent = 4)
    

if __name__ == "__main__":
    yt_api = TranscriptStore()

    print(yt_api.list_available_languages("4O1Fk6edPkI"))
    print(yt_api.get_transcript("4O1Fk6edPkI"))
    print(yt_api.get_segments("4O1Fk6edPkI"))