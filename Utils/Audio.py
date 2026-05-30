# File responsible to hold a class which trasnaltes text into speech

from Utils.Singleton import Singleton
import asyncio
import edge_tts
from Utils.Exception import UnsupportedLanguage
from config import OUTPUT_FOLDER, VOICE_CONFIGS
import os

@Singleton
class Audio:
    def __init__(self):
        pass
           
    def tts(self,TEXT,LANG_ABBREVIATION,OUTPUT_FILE): # LANG - en,hi,es....
        if(TEXT.strip() == ""):
            return True
        
        voice = VOICE_CONFIGS.get(LANG_ABBREVIATION)
        if voice is None:
            raise UnsupportedLanguage(f"[Audio.py:] {LANG_ABBREVIATION} is not supported.")
        
        OUTPUT_FILE = os.path.join(OUTPUT_FOLDER,OUTPUT_FILE)
        
        communicate = edge_tts.Communicate(TEXT, voice)
        asyncio.run(communicate.save(OUTPUT_FILE))
        return True