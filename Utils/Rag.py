import os
import uuid
from qdrant_client import QdrantClient, models
import logging
from dotenv import load_dotenv
from Utils.Singleton import Singleton
from fastembed import TextEmbedding, SparseTextEmbedding

load_dotenv()

@Singleton
class Rag:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("CLUSTER_ENDPOINT"), 
            api_key=os.getenv("QUADRANT_API_KEY")
        )
        self.collection_name = "test" 
        
        self.dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")

    def initialize_collection(self):
        if not self.client.collection_exists(collection_name=self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": models.VectorParams(size=384, distance=models.Distance.COSINE) 
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
                }
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="video_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            logging.getLogger(__name__).info(f"Collection '{self.collection_name}' successfully created.")
        else:
            logging.getLogger(__name__).info(f"Collection '{self.collection_name}' already exists.")

    def video_exists(self, video_id: str) -> bool:
        try:
            count_result = self.client.count(
                collection_name=self.collection_name,
                count_filter=models.Filter(
                    must=[models.FieldCondition(key="video_id", match=models.MatchValue(value=video_id))]
                ),
                exact=True
            )
            return count_result.count > 0
        except Exception as e:
            logging.getLogger(__name__).exception(f"Error checking if video exists: {e}")
            return False
        

    def remake_segments(self, data_segment:list[dict],chunk_size: int = 100, overlap:int = 20):
        all_words = []
        for segment in data_segment.get("segments", []):
            words = segment["text"].split()
            if not words:
                continue
            
            time_per_word = segment["duration"] / len(words)
            current_time = segment["start"]
            
            for word in words:
                all_words.append({
                    "text": word,
                    "start": current_time,
                    "end": current_time + time_per_word
                })
                current_time += time_per_word


        new_larger_segments = []
        i = 0
        step_size = chunk_size - overlap if (chunk_size - overlap) > 0 else chunk_size 
        
        while i < len(all_words):
            chunk = all_words[i : i + chunk_size]
            
            chunk_text = " ".join([w["text"] for w in chunk])
            chunk_start = chunk[0]["start"]
            chunk_end = chunk[-1]["end"]
            
            new_larger_segments.append({
                "text": chunk_text,
                "start": chunk_start,
                "duration": chunk_end - chunk_start
            })
            
            i += step_size

        data_segment["segments"] = new_larger_segments
        return data_segment

    def process_and_store_transcript(self, data_segment: list[dict],VIDEO_ID:str=None):
        if not data_segment:
            return
        
        video_id = data_segment["video_id"]
        if self.video_exists(video_id):
            logging.getLogger(__name__).info(f"Transcript for video '{video_id}' is already stored. Skipping.")
            return
        
        logging.getLogger(__name__).info(f"Processing new video: {video_id}...")

        data_segment = self.remake_segments(data_segment)
        
        texts = [segment['text'] for segment in data_segment["segments"]]
        
        dense_embeddings = [vector.tolist() for vector in self.dense_model.embed(texts)]
        sparse_embeddings = [
            models.SparseVector(indices=sparse.indices.tolist(), values=sparse.values.tolist())
            for sparse in self.sparse_model.embed(texts)
        ]

        points = []
        for i, segment in enumerate(data_segment["segments"]):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{data_segment['video_id']}_{i}"))
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={
                        "dense": dense_embeddings[i],
                        "sparse": sparse_embeddings[i],
                    },
                    payload={
                        "video_id": data_segment['video_id'],
                        "text": segment['text'],
                        "start_time": segment.get('start'),
                        "duration": segment.get('duration')
                    }
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        logging.getLogger(__name__).info(f"Stored transcript for video: {data_segment['video_id']}")
        return f"Transcript Generated for : {VIDEO_ID}."

    def hybrid_search(self, video_id: str, user_query: str, limit: int = 5):
        query_dense = list(self.dense_model.embed([user_query]))[0].tolist()
        
        sparse_res = list(self.sparse_model.embed([user_query]))[0]
        query_sparse = models.SparseVector(
            indices=sparse_res.indices.tolist(), 
            values=sparse_res.values.tolist()
        )

        video_filter = models.Filter(
            must=[models.FieldCondition(key="video_id", match=models.MatchValue(value=video_id))]
        )

        prefetch_limit = limit * 5
        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(query=query_dense, using="dense", limit=prefetch_limit, filter=video_filter),
                models.Prefetch(query=query_sparse, using="sparse", limit=prefetch_limit, filter=video_filter)
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
        )
        return response.points
    

if __name__=="__main__":
    import json
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

    logger = logging.getLogger(__name__)
    for op in output:
        logger.debug(op)