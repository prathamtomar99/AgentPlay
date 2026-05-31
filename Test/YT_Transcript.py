# Testing file for Utils/YT_Transcript

from Utils.YT_Transcript import TranscriptStore
import json

yt_api = TranscriptStore()

# print(yt_api.list_available_languages("4O1Fk6edPkI"))
langs= yt_api.list_available_languages("ZxkNKa5L22Y")
print(langs)
data_yt= yt_api.get_segments("ZxkNKa5L22Y")
data_yt_dict = json.loads(data_yt)
print(data_yt[:10000])

# print(data_yt_dict["language"])
# print(data_yt_dict["video_id"])
# print(data_yt_dict["segments"])