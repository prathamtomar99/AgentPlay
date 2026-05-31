# Testing file for Utils/Translation

import os
from Utils.Audio import Audio
from Utils.Translation import TranslatorAgent
from config import MAX_WORKERS, OUTPUT_FOLDER
from concurrent.futures import ThreadPoolExecutor
import json
import logging

def pipeline(PREVIOUS_SEGMENT, CURRENT_SEGMENT, FUTURE_SEGMENT, TARGET_LANGUAGE_ABBREVIATION,FILE_NAME): # TARGET_LANGUAGE = 'hi' / 'en' etc
    try:
        # translate
        TRANSLATED_TEXT = TranslatorAgent().call(
            PREVIOUS_SEGMENT=PREVIOUS_SEGMENT, 
            CURRENT_SEGMENT=CURRENT_SEGMENT, 
            FUTURE_SEGMENT=FUTURE_SEGMENT, 
            TARGET_LANGUAGE_ABBREVIATION= TARGET_LANGUAGE_ABBREVIATION,
        )
        
        # tts
        os.makedirs(os.path.join("Data"), exist_ok=True)
        Audio().tts(
            TEXT = TRANSLATED_TEXT,
            LANG_ABBREVIATION=TARGET_LANGUAGE_ABBREVIATION,
            OUTPUT_FILE= os.path.join('Data',FILE_NAME),
        )
    except Exception as e:
        return f"Error in {FILE_NAME} : {e}"

    logging.getLogger(__name__).info(f"Completed for: {FILE_NAME}")
    return f"Completed : {FILE_NAME}" 

# # SETUP 1
# if __name__ == "__main__":
#     if not os.path.exists("OUTPUT_FOLDER"):
#        os.mkdir("OUTPUT_FOLDER")

#     PREVIOUS_SEGMENT = "The research team completed the prototype testing phase last week."
#     CURRENT_SEGMENT = "The system now processes multilingual audio streams in real time with low latency."
#     FUTURE_SEGMENT = "It will be deployed across edge devices globally."
#     TARGET_LANGUAGE_ABBREVIATION = "Hi"
#     FILE_NAME = "segment1.mp3"
    
#     executer.submit(pipeline, PREVIOUS_SEGMENT, CURRENT_SEGMENT, FUTURE_SEGMENT, TARGET_LANGUAGE_ABBREVIATION,"1.mp3")
#     executer.shutdown()


# # SETUP 2
if __name__ == "__main__":

    if not os.path.exists(OUTPUT_FOLDER):
        os.mkdir(OUTPUT_FOLDER)
    
    # fs = open("test_json.json","r")
    # data_json = fs.read()
    # fs.close()

    data_json = None
    with open("test_json.json","r") as f:
        data = json.load(f)
    
    futures = []

    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executer:
        for elem in data:
            PREVIOUS_SEGMENT = data[elem]["PREVIOUS_SEGMENT"]
            CURRENT_SEGMENT = data[elem]["CURRENT_SEGMENT"]
            FUTURE_SEGMENT = data[elem]["FUTURE_SEGMENT"]
            TARGET_LANGUAGE_ABBREVIATION = 'hi'

            futures.append(executer.submit(pipeline, PREVIOUS_SEGMENT, CURRENT_SEGMENT, FUTURE_SEGMENT, TARGET_LANGUAGE_ABBREVIATION,elem+".mp3"))
        
        executer.shutdown(wait = True)

        for future in futures:
            try:
                logging.getLogger(__name__).info(future.result())
            except Exception as e:
                logging.getLogger(__name__).exception(e)