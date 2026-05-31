# Testing file for Utils/YT_Transcript

from Utils.YT_Transcript import TranscriptStore
import json
import logging

yt_api = TranscriptStore()

logger = logging.getLogger(__name__)

# logger info for available languages
langs = yt_api.list_available_languages("ZxkNKa5L22Y")
logger.info(langs)
data_yt = yt_api.get_segments("ZxkNKa5L22Y")
data_yt_dict = json.loads(data_yt)
logger.debug(data_yt[:10000])

# print(data_yt_dict["language"])
# print(data_yt_dict["video_id"])
# print(data_yt_dict["segments"])