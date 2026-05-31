import json
from Utils.Rag import Rag

rag_obj = Rag()
rag_obj.initialize_collection()

from Utils.YT_Transcript import TranscriptStore
import json

yt_api = TranscriptStore()

yt_data = json.loads(yt_api.get_segments("ZxkNKa5L22Y"))
# with open("yt_original.txt",'w') as fs:
#     json.dump(yt_data,fs,indent=4)
# print(yt_data)

yt_remake_data = rag_obj.remake_segments(yt_data)
# with open("yt_remake.txt",'w') as fs:
#     json.dump(yt_remake_data,fs,indent=4)
# print(yt_remake_data)

rag_obj.process_and_store_transcript(data_segment=yt_data)

output = rag_obj.hybrid_search(video_id=yt_data["video_id"],user_query="what is idea of nation")

for op in output:
    print(op)