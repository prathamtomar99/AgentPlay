from Utils.Audio import Audio
import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from config import MAX_WORKERS,OUTPUT_FOLDER

executer = ProcessPoolExecutor(max_workers = MAX_WORKERS)

audio_obj = Audio()

def pipeline(text,lang,FILE_NAME):
    # translate
    # tts
    
    audio_obj.tts(text,lang,FILE_NAME)
    return f"Conpleted : {text}" 


if __name__ == "__main__":
    if not os.path.exists("Data/"):
       os.mkdir("Data/")

    # asyncio.run(audio_obj.tts("This is Pratham","en","test.mp3"))
    
    print(executer.submit(pipeline,"This is Pratham","en","test2.mp3"))
    executer.shutdown()